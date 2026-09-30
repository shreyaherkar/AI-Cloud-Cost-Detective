import boto3


def validate_credentials(access_key, secret_key, region):

    try:

        session = boto3.Session(
            aws_access_key_id=access_key,
            aws_secret_access_key=secret_key,
            region_name=region
        )

        sts = session.client("sts")

        identity = sts.get_caller_identity()

        return {
            "success": True,
            "session": session,
            "account": identity["Account"],
            "arn": identity["Arn"]
        }
    except Exception as e:
        return {
            "success": False,
            "error": str(e)
            }
