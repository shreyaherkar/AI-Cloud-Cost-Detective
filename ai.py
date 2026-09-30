import os
import json

from dotenv import load_dotenv
from openai import OpenAI


load_dotenv()


client = OpenAI(

    api_key=os.getenv("GROQ_API_KEY"),

    base_url="https://api.groq.com/openai/v1"

)


MODEL = "llama-3.3-70b-versatile"


def call_ai(system_prompt, user_prompt):

    try:

        response = client.chat.completions.create(

            model=MODEL,

            messages=[

                {
                    "role":"system",
                    "content":system_prompt
                },

                {
                    "role":"user",
                    "content":user_prompt
                }

            ],

            temperature=0.3,

            max_tokens=1500

        )


        answer = response.choices[0].message.content


        if not answer:
            raise Exception("Empty AI response")


        return answer.strip()


    except Exception as e:

        print("========== GROQ AI ERROR ==========")
        print(e)
        print("===================================")

        return "The AI service is temporarily unavailable. Please try again later."


def generate_ai_summary(cost_data, resources):


    prompt = f"""

Analyze this AWS environment as a Senior AWS Solutions Architect.


AWS COST

Total Monthly Cost:
${cost_data.get("total_cost",0)}


Services:

{cost_data.get("services",[])}



RESOURCE HEALTH

Running EC2:
{resources.get("ec2_running",0)}

Stopped EC2:
{resources.get("ec2_stopped",0)}

S3 Buckets:
{resources.get("s3_buckets",0)}

RDS Instances:
{resources.get("rds_instances",0)}


OPTIMIZATION

Optimization Score:
{resources.get("optimization_score",0)}/100

Resource Health:
{resources.get("resource_health","Unknown")}

Estimated Monthly Savings:
${resources.get("estimated_monthly_savings",0)}



Write a professional executive summary.

Rules:

- Maximum 180 words
- Mention cost observations
- Mention optimization opportunities
- Mention security concerns if present
- No markdown headings

"""


    return call_ai(

        "You are a Senior AWS Cloud Architect and FinOps expert.",

        prompt

    )


def generate_ai_recommendations(cost_data, resources):

    

    prompt = f"""
You are an AWS FinOps expert.

Analyze this AWS environment and return ONLY valid JSON.

AWS Cost Data:
{cost_data}

AWS Resources:
{resources}

Return this exact JSON format:

{{
    "monthly_cost": "$0.00",
    "highest_cost_service": "EC2",
    "estimated_savings": "$0",
    "risk_level": "Low",
    "optimization_score": 80,
    "recommendations": [
        "Recommendation 1",
        "Recommendation 2",
        "Recommendation 3"
    ]
}}
"""


    try:

        response = client.chat.completions.create(

            model=MODEL,

            messages=[
                {
                    "role": "user",
                    "content": prompt
                }
            ],

            temperature=0.2
        )


        result = response.choices[0].message.content

        result = result.replace("```json", "")
        result = result.replace("```", "")
        result = result.strip()



        try:

            data = json.loads(result)
            if not validate_ai_json(data):
                raise ValueError("Invalid AI JSON response")


        except Exception:

            print("RAW AI RESPONSE:")
            print(result)


            data = {

                "monthly_cost": "$0",

                "highest_cost_service": "Unknown",

                "estimated_savings": "$0",

                "risk_level": "Low",

                "optimization_score": 0,

                "recommendations": [

                    "AI response format issue",

                    "Please retry analysis"

                ]

            }



        required_keys = [

            "monthly_cost",

            "highest_cost_service",

            "estimated_savings",

            "risk_level",

            "optimization_score",

            "recommendations"

        ]
        for key in required_keys:
            if key not in data:
                if key == "recommendations":
                    data[key] = []

                elif key == "optimization_score":
                    data[key] = 0

                else:
                    data[key] = "N/A"



        return data

    except Exception as e:
        return {

            "monthly_cost": "$0",

            "highest_cost_service": "Unknown",

            "estimated_savings": "$0",

            "risk_level": "Unknown",

            "optimization_score": 0,

            "recommendations": [

                "Unable to generate AI recommendations."

        ],

        "error": str(e)

    }


def chat_with_ai(user_question, cost_data, resources):


    prompt = f"""

You are an expert AI Cloud Assistant.

You have knowledge in:

- AWS
- Cloud Computing
- DevOps
- Kubernetes
- Docker
- Terraform
- Linux
- Networking
- Databases
- Python
- System Design
- Artificial Intelligence
- Cyber Security



You also have access to the user's CURRENT AWS environment.



================================================
AWS ACCOUNT CONTEXT
================================================


MONTHLY COST

Total:

${cost_data.get("total_cost",0)}



Services:

{cost_data.get("services",[])}




RESOURCE INVENTORY


Running EC2:

{resources.get("ec2_running",0)}


Stopped EC2:

{resources.get("ec2_stopped",0)}


S3 Buckets:

{resources.get("s3_buckets",0)}


RDS Instances:

{resources.get("rds_instances",0)}




COST OPTIMIZATION


Optimization Score:

{resources.get("optimization_score",0)}/100


Resource Health:

{resources.get("resource_health","Unknown")}


Estimated Savings:

${resources.get("estimated_monthly_savings",0)}



Idle Findings:

{resources.get("idle_findings",[])}



Security Findings:

{resources.get("security",{})}



================================================
USER QUESTION
================================================


{user_question}



================================================
RESPONSE RULES
================================================


1. Answer the user's question directly.


2. If AWS-related, use the provided AWS account context when useful.


3. If information is not available in the dashboard, clearly mention that.


4. Still provide general technical guidance.


5. Use Markdown formatting.


6. Use headings and bullet points when helpful.


7. Provide practical examples.


8. Keep answers professional and accurate.



"""


    return call_ai(

        "You are ChatGPT-level AI assistant specialized in Cloud and DevOps.",

        prompt

    )


def validate_ai_json(data):


    required_fields = [

        "monthly_cost",

        "highest_cost_service",

        "estimated_savings",

        "optimization_score",

        "risk_level",

        "recommendations"

    ]


    for field in required_fields:


        if field not in data:


            return False



    if not isinstance(

        data["recommendations"],

        list

    ):


        return False



    return True


def get_ai_status():


    if os.getenv("GROQ_API_KEY"):


        return {

            "status":"Available",

            "provider":"Groq",

            "model":MODEL

        }



    return {

        "status":"API Key Missing",

        "provider":"Groq",

        "model":MODEL

    }

