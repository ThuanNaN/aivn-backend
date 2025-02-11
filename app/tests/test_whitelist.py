from app.core.database import mongo_db
import asyncio
import pandas as pd

try:
    user_collection = mongo_db["users"]
    whitelist_collection = mongo_db["whitelists"]
except Exception as e:
    exit(1)


registrant_file = './app/tests/registrant_template.csv'


async def check_whitelist():
    
    db_whitelist = []
    async for doc in whitelist_collection.find():
        db_whitelist.append(doc['email'])


    df = pd.read_csv(registrant_file)
    new_whitelist = df.iloc[:, 0].tolist()
    # Normalize email to lower case
    new_whitelist = [email.lower() for email in new_whitelist]

    email_need_to_add = list(set(new_whitelist) - set(db_whitelist))
    not_in_new_whitelist = list(set(db_whitelist) - set(new_whitelist))

    print("Current whitelist: ", len(db_whitelist))
    print("New whitelist: ", len(new_whitelist))
    print("Email need to add: ", len(email_need_to_add))
    print("Email not in new whitelist: ", not_in_new_whitelist)


async def check_role_of_whitelist():
    current_users = []
    async for doc in user_collection.find():
        current_users.append({
            "email": doc['email'],
            "role": doc['role']
        })
    
    whitelist = []
    async for doc in whitelist_collection.find():
        whitelist.append(doc['email'])
    
    # print which user in whitelist but not in role "aio"
    for email in whitelist:
        for user in current_users:
            if user['email'] == email and user['role'] != "aio":
                print(email, user['role'])

if __name__ == '__main__':
    asyncio.run(check_whitelist())
    asyncio.run(check_role_of_whitelist())
