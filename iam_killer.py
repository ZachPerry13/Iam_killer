"""
Finds vault-approle-slides-app-qa and vault-approle-monocle-staging users over a week old 
that have never been used and deletes them.
This is the most cautious way to run it. We can probably delete slides qa users
even if they have been used if they are more than a few days old. Script doesn't
take any parameters but you can flip some flags to delete all types of users who
have not been used, or delete users even if they have been used. It won't let you
do both because that's probably a mistake.
"""

import boto3
import re
import datetime
import sys

IAM_CLIENT = boto3.client("iam")
IAM_RESOURCE = boto3.resource("iam")
POLICY_ARN_QA = "arn:aws:iam::241984356181:policy/slidesapp-access"
POLICY_ARN_MONOCLE = "arn:aws:iam::241984356181:policy/monocle-staging"
# Only look at users older than this many days
DAYS_TO_PRESERVE = 3
# Batch size.
USERS_PER_REQUEST = 1000
#Leave this false
ALL_APPS = False
# By default only deletes users that have never been used.
ONLY_UNUSED = False
# Set this to False to actually do the delete rather than just say it will.
DRYRUN = False

# These could be made into one function that takes in the Policy_ARN as an arguement :shrug:
def delete_user_qa(user_name, access_key):
    """ Delete a user. First detaches policy and removes the access key. Otherwise
    delete will fail."""
    IAM_CLIENT.detach_user_policy(UserName=user_name, PolicyArn=POLICY_ARN_QA)
    IAM_CLIENT.delete_access_key(UserName=user_name, AccessKeyId=access_key)
    IAM_CLIENT.delete_user(UserName=user_name)

def delete_user_Monocle(user_name, access_key):
    """ Delete a user. First detaches policy and removes the access key. Otherwise
    delete will fail."""
    IAM_CLIENT.detach_user_policy(UserName=user_name, PolicyArn=POLICY_ARN_MONOCLE)
    IAM_CLIENT.delete_access_key(UserName=user_name, AccessKeyId=access_key)
    IAM_CLIENT.delete_user(UserName=user_name)

#Searches for users matching the string vault-approle-slides-app-qa* then makes an array of any older than the amount of days specified 
def kill_users_qa():
    cutoff = datetime.date.today() - datetime.timedelta(days=DAYS_TO_PRESERVE)
    params = {"MaxItems": USERS_PER_REQUEST}
    done = marker = ""
    while not done:
        response = IAM_CLIENT.list_users(**params)
        done = not response["IsTruncated"]
        if not done:
            params["Marker"] = response["Marker"]
        for user in response["Users"]:
            user_name = user["UserName"]
            if ALL_APPS or re.search(r"^vault-approle-slides-app-qa", user_name):
                if user["CreateDate"].date() < cutoff:
                    # detach policy
                    # remove access key
                    key_response = IAM_CLIENT.list_access_keys(UserName=user_name)
                    access_keys = [
                        m["AccessKeyId"] for m in key_response["AccessKeyMetadata"]
                    ]
                    if len(access_keys) != 1:
                        print(
                            f"Got {len(access_keys)} keys for {user_name}. This is unexpected and no action will be taken for this user"
                        )
                        continue

                    access_key = access_keys[0]
                    last_used = IAM_CLIENT.get_access_key_last_used(
                        AccessKeyId=access_key
                    )
                    if ONLY_UNUSED and "LastUsedDate" in last_used["AccessKeyLastUsed"]:
                        print(
                            f"Key for {user_name} has been used. No action will be taken."
                        )
                        continue

                    print(f"User {user_name} ({user['CreateDate']})...deleting.")
                    if not DRYRUN:
                        delete_user_qa(user_name, access_key)

#Searches for users matching the string vault-approle-monocle-staging* then makes an array of any older than the amount of days specified 
def kill_users_monocole_staging():
    cutoff = datetime.date.today() - datetime.timedelta(days=DAYS_TO_PRESERVE)
    params = {"MaxItems": USERS_PER_REQUEST}
    done = marker = ""
    while not done:
        response = IAM_CLIENT.list_users(**params)
        done = not response["IsTruncated"]
        if not done:
            params["Marker"] = response["Marker"]
        for user in response["Users"]:
            user_name = user["UserName"]
            if ALL_APPS or re.search(r"^vault-approle-monocle-staging", user_name):
                if user["CreateDate"].date() < cutoff:
                    # detach policy
                    # remove access key
                    key_response = IAM_CLIENT.list_access_keys(UserName=user_name)
                    access_keys = [
                        m["AccessKeyId"] for m in key_response["AccessKeyMetadata"]
                    ]
                    if len(access_keys) != 1:
                        print(
                            f"Got {len(access_keys)} keys for {user_name}. This is unexpected and no action will be taken for this user"
                        )
                        continue

                    access_key = access_keys[0]
                    last_used = IAM_CLIENT.get_access_key_last_used(
                        AccessKeyId=access_key
                    )
                    if ONLY_UNUSED and "LastUsedDate" in last_used["AccessKeyLastUsed"]:
                        print(
                            f"Key for {user_name} has been used. No action will be taken."
                        )
                        continue

                    print(f"User {user_name} ({user['CreateDate']})...deleting.")
                    if not DRYRUN:
                        delete_user_Monocle(user_name, access_key)

if __name__ == "__main__":
    if ALL_APPS and not ONLY_UNUSED:
        print(f"Delete all users older than {DAYS_TO_PRESERVE}? This is not safe!")
    else:
        kill_users_qa()
        kill_users_monocole_staging()