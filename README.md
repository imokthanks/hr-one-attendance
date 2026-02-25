# Attendance_HRONE

Automatically mark attendance everyday on your behalf using GitHub Actions. This script automates the process of marking attendance in HROne system by running twice daily at configured times.

## Features

- Automatic attendance marking at configured times (9:00 AM and 6:00 PM IST)
- Holiday and weekend detection
- Leave detection
- GitHub Actions automation
- Environment variable based configuration

## Setup

1. Fork this repository
2. Add the following secrets to your GitHub repository:
   - `HRONE_USERNAME`: Your HROne username
   - `HRONE_PASSWORD`: Your HROne password
   - `EMPLOYEE_ID`: Your HROne employee ID

## Requirements

- Python 3.x
- Required packages:
  ```
  requests
  python-dateutil
  ```

## Local Development

1. Clone the repository:
   ```bash
   git clone https://github.com/yourusername/Attendance_HRONE.git
   cd Attendance_HRONE
   ```

2. Create a virtual environment and install dependencies:
   ```bash
   python -m venv venv
   source venv/bin/activate  # On Windows use: venv\Scripts\activate
   pip install -r requirements.txt
   ```

3. Set up environment variables:
   ```bash
   export HRONE_USERNAME="your_username"
   export HRONE_PASSWORD="your_password"
   export EMPLOYEE_ID="your_employee_id"
   ```

4. Run the script:
   ```bash
   python main.py
   ```

## GitHub Actions Configuration

The workflow is configured to run automatically at:
- 9:00 AM IST 
- 6:00 PM IST 

You can also trigger the workflow manually from the GitHub Actions tab.

## Notes

- The script checks for holidays and leaves before marking attendance
- Make sure your credentials are kept secure and not shared
- The script uses IST (Indian Standard Time) for all operations

## License

MIT License
