import boto3

from datetime import datetime, timedelta

from botocore.exceptions import ClientError


def get_session(access_key, secret_key, region):

    return boto3.Session(

        aws_access_key_id=access_key,

        aws_secret_access_key=secret_key,

        region_name=region

    )


def get_cost_data(access_key, secret_key, region):

    try:

        session = get_session(
            access_key,
            secret_key,
            region
        )


        ce = session.client("ce")


        end = datetime.utcnow().date()

        start = end.replace(day=1)



        response = ce.get_cost_and_usage(

            TimePeriod={

                "Start": str(start),

                "End": str(end + timedelta(days=1))

            },

            Granularity="MONTHLY",

            Metrics=[

                "UnblendedCost"

            ],

            GroupBy=[

                {

                    "Type": "DIMENSION",

                    "Key": "SERVICE"

                }

            ]

        )



        services = []

        total_cost = 0



        groups = response["ResultsByTime"][0]["Groups"]



        for group in groups:


            service = group["Keys"][0]


            amount = float(

                group["Metrics"]

                ["UnblendedCost"]

                ["Amount"]

            )


            total_cost += amount



            services.append(

                {

                    "service": service,

                    "cost": round(amount,2)

                }

            )



        services.sort(

            key=lambda x:x["cost"],

            reverse=True

        )



        return {


            "total_cost": round(total_cost,2),


            "services": services


        }



    except Exception as e:


        return {


            "total_cost":0,


            "services":[],


            "error":str(e)


        }


def analyze_resources(access_key, secret_key, region):

    session = get_session(
        access_key,
        secret_key,
        region
    )


    ec2 = session.client("ec2")

    s3 = session.client("s3")

    rds = session.client("rds")



    resources = {


        "ec2_running": 0,

        "ec2_stopped": 0,


        "s3_buckets": 0,

        "rds_instances": 0,


        "unused_ebs": 0,

        "unused_eips": 0,

        "old_snapshots": 0,


        "idle_ec2": [],

        "idle_findings": [],


        "estimated_monthly_savings": 0,


        "security": {},


        "optimization_score": 100,


        "resource_health": "Excellent"


    }



    estimated_savings = 0

    try:


        paginator = ec2.get_paginator(
            "describe_instances"
        )


        for page in paginator.paginate():


            for reservation in page["Reservations"]:


                for instance in reservation["Instances"]:


                    instance_id = instance["InstanceId"]


                    state = instance["State"]["Name"]



                    if state == "running":

                        resources["ec2_running"] += 1



                    elif state == "stopped":


                        resources["ec2_stopped"] += 1


                        resources["idle_ec2"].append(

                            instance_id

                        )


                        resources["idle_findings"].append(

                            {

                                "type":"Idle EC2",

                                "resource":instance_id,

                                "severity":"Medium"

                            }

                        )


                        estimated_savings += 20



    except ClientError as e:


        resources["idle_findings"].append(

            {

                "type":"EC2 Analysis Error",

                "resource":"AWS API",

                "severity":"Low",

                "message":str(e)

            }

        )

    try:


        paginator = ec2.get_paginator(

            "describe_volumes"

        )


        for page in paginator.paginate():


            for volume in page["Volumes"]:


                volume_id = volume["VolumeId"]



                if len(volume["Attachments"]) == 0:


                    resources["unused_ebs"] += 1



                    resources["idle_findings"].append(

                        {

                            "type":"Unused EBS",

                            "resource":volume_id,

                            "severity":"Medium"

                        }

                    )


                    estimated_savings += 5



    except ClientError as e:


        resources["idle_findings"].append(

            {

                "type":"EBS Analysis Error",

                "resource":"AWS API",

                "severity":"Low",

                "message":str(e)

            }

        )

    try:

        addresses = ec2.describe_addresses()["Addresses"]


        for address in addresses:


            allocation_id = address.get(

                "AllocationId",

                "Unknown"

            )


            if "AssociationId" not in address:


                resources["unused_eips"] += 1


                resources["idle_findings"].append(

                    {

                        "type":"Unused Elastic IP",

                        "resource":allocation_id,

                        "severity":"Low"

                    }

                )


                estimated_savings += 4



    except ClientError as e:


        resources["idle_findings"].append(

            {

                "type":"Elastic IP Analysis Error",

                "resource":"AWS API",

                "severity":"Low",

                "message":str(e)

            }

        )

    try:


        snapshots = ec2.describe_snapshots(

            OwnerIds=["self"]

        )["Snapshots"]



        cutoff = datetime.utcnow() - timedelta(days=30)



        for snapshot in snapshots:


            snapshot_id = snapshot["SnapshotId"]


            snapshot_date = snapshot["StartTime"].replace(

                tzinfo=None

            )



            if snapshot_date < cutoff:


                resources["old_snapshots"] += 1



                resources["idle_findings"].append(

                    {

                        "type":"Old Snapshot",

                        "resource":snapshot_id,

                        "severity":"Low"

                    }

                )


                estimated_savings += 1



    except ClientError as e:


        resources["idle_findings"].append(

            {

                "type":"Snapshot Analysis Error",

                "resource":"AWS API",

                "severity":"Low",

                "message":str(e)

            }

        )

    try:


        buckets = s3.list_buckets()["Buckets"]


        resources["s3_buckets"] = len(buckets)


    except ClientError as e:
        resources["s3_buckets"] = 0
        resources["idle_findings"].append({
            "type": "S3 Analysis Error",
            "resource": "AWS API",
            "severity": "Low",
            "message": str(e)
            })

    try:


        databases = rds.describe_db_instances()[

            "DBInstances"

        ]


        resources["rds_instances"] = len(databases)



    except ClientError as e:
        resources["rds_instances"] = 0
        resources["idle_findings"].append({

            "type": "RDS Analysis Error",

            "resource": "AWS API",

            "severity": "Low",

            "message": str(e)

    })

    security = {

        "public_s3": [],

        "open_security_groups": [],

        "mfa_status": "Unknown",

        "account_access_status": "Unknown"

    }

    try:


        buckets = s3.list_buckets()["Buckets"]



        for bucket in buckets:


            bucket_name = bucket["Name"]


            try:


                block = s3.get_public_access_block(

                    Bucket=bucket_name

                )


                config = block[

                    "PublicAccessBlockConfiguration"

                ]



                if not all(config.values()):


                    security["public_s3"].append(

                        bucket_name

                    )


            except ClientError:


                pass



    except ClientError:


        pass

    try:


        security_groups = ec2.describe_security_groups()[

            "SecurityGroups"

        ]



        open_groups = set()



        for sg in security_groups:


            group_id = sg["GroupId"]



            for permission in sg["IpPermissions"]:


                for ip_range in permission.get(

                    "IpRanges",

                    []

                ):


                    if ip_range.get(

                        "CidrIp"

                    ) == "0.0.0.0/0":


                        open_groups.add(

                            group_id

                        )



        security["open_security_groups"] = list(

            open_groups

        )



    except ClientError:


        pass

    try:


        iam = session.client("iam")



        summary = iam.get_account_summary()[

            "SummaryMap"

        ]



        if summary.get(

            "AccountMFAEnabled",

            0

        ) == 1:


            security["mfa_status"] = "Enabled"


        else:


            security["mfa_status"] = "Disabled"



        if summary.get(

            "AccountAccessKeysPresent",

            0

        ) == 1:


            security["account_access_status"] = (

                "Access Keys Present"

            )


        else:


            security["account_access_status"] = (

                "No Root Access Keys"

            )



    except ClientError:


        security["mfa_status"] = (

            "Permission Required"

        )



    resources["security"] = security

    resources["estimated_monthly_savings"] = round(

        estimated_savings,

        2

    )

    score = 100



    score -= resources["ec2_stopped"] * 5

    score -= resources["unused_ebs"] * 8

    score -= resources["unused_eips"] * 6

    score -= resources["old_snapshots"] * 2



    score -= len(

        security["public_s3"]

    ) * 10



    score -= len(

        security["open_security_groups"]

    ) * 10



    if score < 0:

        score = 0



    resources["optimization_score"] = score

    issues = (

        resources["ec2_stopped"]

        +

        resources["unused_ebs"]

        +

        resources["unused_eips"]

        +

        resources["old_snapshots"]

        +

        len(security["public_s3"])

        +

        len(security["open_security_groups"])

    )



    if issues == 0:


        resources["resource_health"] = "Excellent"



    elif issues <= 3:


        resources["resource_health"] = "Good"



    elif issues <= 7:


        resources["resource_health"] = "Needs Optimization"



    else:


        resources["resource_health"] = "Critical"

    resources["idle_summary"] = {


        "total_idle_resources": issues,


        "estimated_waste":

            resources["estimated_monthly_savings"],



        "recommendation":

            (

                "Review and remove unused AWS resources."

                if issues > 0

                else

                "No major idle resources detected."

            )

    }

    return resources

