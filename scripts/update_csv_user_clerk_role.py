import subprocess
import json
from pandas import read_csv
import numpy as np

user_data = read_csv('./registrant_template.csv')

emails = np.array(user_data.iloc[:, 0])
nicknames = np.array(user_data.iloc[:, 1])


TOKEN = ""

for i, (email, name) in enumerate(zip(emails, nicknames)):
    data = json.dumps({
        "email": email,
        "nickname": name
    })
    curl_command = [
        "curl",
        "-X", "POST",
        "-H", "Content-Type: application/json",
        "-H", f"Authorization: Bearer {TOKEN}",
        "-d", data,
        "http://localhost:8000/api/v1/user/whitelist"
    ]
    result = subprocess.run(curl_command, capture_output=True, text=True)

    print("Status Code:", result.returncode, "i = ", i)
    print("Output:", result.stdout)
    print("Error:", result.stderr)