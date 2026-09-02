import requests
import json
import os
from datetime import datetime, time
import pytz
import argparse
# from dotenv import load_dotenv

# load_dotenv()

USERNAME = os.environ.get("HRONE_USERNAME", "")
PASSWORD = os.environ.get("HRONE_PASSWORD", "")
EMPLOYEE_ID = os.environ.get("EMPLOYEE_ID", "")
NTFY_TOPIC = os.environ.get("NTFY_TOPIC", "dharahas-attendance-hrone")

ist = pytz.timezone("Asia/kolkata")


def notify(title: str, message: str, priority: str = "default", tags: str = ""):
    try:
        headers = {"Title": title, "Priority": priority}
        if tags:
            headers["Tags"] = tags
        requests.post(f"https://ntfy.sh/{NTFY_TOPIC}", data=message.encode("utf-8"), headers=headers)
    except Exception as e:
        print(f"Notification failed: {e}")


def get_punch_time() -> datetime:
    override = os.environ.get("PUNCH_TIME", "").strip()
    if override:
        return override
    now_ist = datetime.now(ist)
    # if now_ist.hour < 12:
    #     fixed_time = now_ist.replace(hour=9, minute=30, second=0, microsecond=0)
    # else:
    #     fixed_time = now_ist.replace(hour=18, minute=30, second=0, microsecond=0)
    return now_ist


def get_access_token(username: str, password: str):
    """Login and return session with JWT cookie"""
    session = requests.Session()
    url = "https://gateway.hrone.cloud/oauth2/token"
    payload = f"username={username}&password={password}&grant_type=password&loginType=1&companyDomainCode=popcornapps&isUpdated=0&validSource=Y&deviceName=MS-Edge-Chromium-windows-10"

    headers = {
        "accept": "application/json, text/plain, */*",
        "content-type": "application/x-www-form-urlencoded",
        "domaincode": "popcornapps",
    }

    response = session.post(url, headers=headers, data=payload)
    if response.status_code == 200:
        data = response.json()
        user = data.get("userName")
        access_token = data.get("access_token")
        print(f"login successful for username: {user}")
        
        # Set the access token as JwtTokenCookie
        session.cookies.set("JwtTokenCookie", access_token, domain=".hrone.cloud")
        return session
    else:
        print("Login failed:", response.status_code, response.text)
        return None

def within_limits(punch_time: datetime):
    if (
        time(9, 0) <= punch_time.time() <= time(10, 0)
        or
        time(18, 0) <= punch_time.time() <= time(19, 0)
    ):
        return True
    return False


def mark_attendance(session, employee_id, skip_limit_check: bool):
    url = "https://app.hrone.cloud/api/timeoffice/mobile/checkin/Attendance/Request"
    punch_time = get_punch_time()
    if (not skip_limit_check and not within_limits(punch_time)):
        print(f"Attendance not within limits, attempted to punch at {punch_time.strftime("%Y-%m-%dT%H:%M")}")
        notify("Attendance not within limits", f"Attempted to punch at {punch_time.strftime("%Y-%m-%dT%H:%M")}", priority="high", tags="x")
        return
    punch_time = punch_time.strftime("%Y-%m-%dT%H:%M")

    payload = {
        "requestType": "A",
        "applyRequestSource": 10,
        "employeeId": int(employee_id),
        "latitude": "",
        "longitude": "",
        "geoAccuracy": "",
        "geoLocation": "",
        "punchTime": punch_time,
        "remarks": "",
        "uploadedPhotoOneName": "",
        "uploadedPhotoOnePath": "",
        "uploadedPhotoTwoName": "",
        "uploadedPhotoTwoPath": "",
        "attendanceSource": "W",
        "attendanceType": "Online",
    }

    headers = {
        "accept": "application/json, text/plain, */*",
        "content-type": "application/json",
        "domaincode": "popcornapps",
    }

    response = session.post(url, headers=headers, data=json.dumps(payload))
    if response.status_code == 200:
        print(f"Attendance marked successfully for {employee_id} at {punch_time}")
        print(response.json())
        notify("Attendance Marked", f"Punched at {punch_time}", tags="white_check_mark")
    else:
        print("Attendance failed:", response.status_code, response.text)
        notify("Attendance Failed", f"Error {response.status_code}: {response.text[:200]}", priority="high", tags="x")


def check_holiday(session: requests.Session, employee_id: int) -> bool:
    url = "https://app.hrone.cloud/api/timeoffice/attendance/Calendar"

    payload = json.dumps(
        {
            "attendanceYear": datetime.now(ist).year,
            "attendanceMonth": datetime.now(ist).month,
            "employeeId": employee_id,
            "calendarViewType": "C",
        }
    )
    headers = {
        "accept": "application/json, text/plain, */*",
        "content-type": "application/json",
        "domaincode": "handyonline",
    }
    today = datetime.now(ist).date()
    response = session.post(url, headers=headers, data=payload)
    if response.status_code == 200:
        data = response.json()
        if (
            data
            and isinstance(data, list)
            and (
                data[today.day - 1].get("updatedFirstHalfStatus") == "HO"
                or data[today.day - 1].get("updatedFirstHalfStatus") == "WO"
            )
        ):
            print(f"Today ({today}) is a holiday/weekend.")
            return True
        else:
            print(f"Today ({today}) is not a holiday/weekend.")
            return False
    else:
        print("Failed to fetch holidays:", response.status_code, response.text)
        return False


def check_leave(session: requests.Session):
    url = "https://app.hrone.cloud/api/Request/InboxRequest/Search"

    payload = json.dumps(
        {
            "actionStatus": 0,
            "inboxRequestTypeId": 0,
            "employeeFilterValue": "",
            "fromDate": "",
            "toDate": "",
            "filterThreeValue": "",
            "filterInsertId": 0,
            "leaveTypes": "",
            "pagination": {"pageNumber": 1, "pageSize": 15},
        }
    )

    headers = {
        "accept": "application/json, text/plain, */*",
        "content-type": "application/json",
        "domaincode": "handyonline",
    }
    response = session.post(url, headers=headers, data=payload)
    if response.status_code == 200:
        data = response.json()
        today = datetime.now(ist).date()
        if data and isinstance(data, list):
            for item in data:
                data_unparsed = item.get("requestSubjectSectionTwo")
                if data_unparsed and isinstance(data_unparsed, str):
                    data_content = data_unparsed.split(" to ")[0].split("/")
                    data_parsed = (
                        f"{data_content[2]}-{data_content[1]}-{data_content[0]}"
                    )
                print(f"Leave request found: {data_parsed}")
                if data_parsed and data_parsed == today.strftime("%Y-%m-%d"):
                    print(f"Leave request found for today : {data_parsed}")
                    return True
        print("No leave requests found for today.")
        return False
    else:
        print("No leave requests found")
        return False

def should_skip_limit_check() -> bool:
    parser = argparse.ArgumentParser()
    parser.add_argument("--trigger", type=str)
    trigger = parser.parse_args().trigger
    return trigger == "workflow_dispatch"


if __name__ == "__main__":
    if not USERNAME or not PASSWORD or not EMPLOYEE_ID:
        print("Please provide all required environment variables.")
        exit(1)

    skip_limit_check = should_skip_limit_check()

    print(f"Processing for {USERNAME} with employee ID {EMPLOYEE_ID}")
    session = get_access_token(USERNAME, PASSWORD)
    if session:
        if not check_holiday(session, EMPLOYEE_ID):
            if not check_leave(session):
                mark_attendance(session, EMPLOYEE_ID, skip_limit_check)
            else:
                print("Leave request found, skipping attendance marking.")
                notify("Attendance Skipped", "Leave request found for today", tags="palm_tree")
        else:
            print("Today is a holiday or weekend, skipping attendance marking.")
            notify("Attendance Skipped", "Today is a holiday or weekend", tags="calendar")
    else:
        print(f"Failed to authenticate for {USERNAME}")
        notify("Attendance Failed", "Login to HROne failed", priority="high", tags="x")
