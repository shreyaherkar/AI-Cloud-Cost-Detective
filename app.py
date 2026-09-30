from flask import (
    Flask,
    render_template,
    request,
    redirect,
    session,
    jsonify
)

import os
from dotenv import load_dotenv

load_dotenv()

from aws_connector import validate_credentials

from aws_cost import (
    get_cost_data,
    analyze_resources
)


from ai import (
    generate_ai_summary,
    generate_ai_recommendations,
    chat_with_ai,
    get_ai_status
)


from budget import get_budget_status


app = Flask(__name__)


app.secret_key = os.getenv(
    "SECRET_KEY",
    os.urandom(24).hex()
)


@app.route("/")
def login():

    return render_template(
        "connect.html"
    )


@app.route("/connect", methods=["POST"])
def connect():


    access_key = request.form.get(
        "access_key",
        ""
    ).strip()


    secret_key = request.form.get(
        "secret_key",
        ""
    ).strip()


    region = request.form.get(
        "region",
        ""
    ).strip()



    result = validate_credentials(

        access_key,

        secret_key,

        region

    )


    if not result["success"]:


        return render_template(

            "connect.html",

            error=result["error"]

        )



    session["access_key"] = access_key

    session["secret_key"] = secret_key

    session["region"] = region



    return redirect("/dashboard")


@app.route("/dashboard")
def dashboard():


    if "access_key" not in session:


        return redirect("/")



    try:


        cost_data = get_cost_data(

            session["access_key"],

            session["secret_key"],

            session["region"]

        )



        resources = analyze_resources(

            session["access_key"],

            session["secret_key"],

            session["region"]

        )

        budget = get_budget_status(

            cost_data.get(

                "total_cost",

                0

            )

        )

        ai_summary = generate_ai_summary(

            cost_data,

            resources

        )



        ai_recommendations = generate_ai_recommendations(

            cost_data,

            resources

        )



        ai_status = get_ai_status()



        return render_template(

            "index.html",

            cost_data=cost_data,

            resources=resources,

            budget=budget,

            ai_summary=ai_summary,

            ai_recommendations=ai_recommendations,

            ai_status=ai_status

        )



    except Exception as e:


        return render_template(

            "index.html",

            cost_data={

                "total_cost":0,

                "services":[]

            },

            resources={

                "ec2_running":0,

                "ec2_stopped":0,

                "s3_buckets":0,

                "rds_instances":0,

                "unused_ebs":0,

                "error":str(e)

            },

            budget={

                "budget":0,

                "spent":0,

                "remaining":0,

                "used_percent":0,

                "status":"Unavailable",

                "color":"gray"

            },

            ai_summary=(

                "Dashboard error: "

                + str(e)

            ),

            ai_recommendations={

                "recommendations":[

                    "Unable to generate AI recommendations."

                ]

            },

            ai_status={

                "status":"Unavailable"

            }

        )


@app.route("/api/chat", methods=["POST"])
def api_chat():


    if "access_key" not in session:


        return jsonify({

            "reply":

            "Please connect your AWS account first."

        }),401



    try:


        data = request.get_json(silent=True) or {}



        question = data.get(

            "message",

            ""

        ).strip()



        if not question:


            return jsonify({

                "reply":

                "Please enter a question."

            })



        cost_data = get_cost_data(

            session["access_key"],

            session["secret_key"],

            session["region"]

        )



        resources = analyze_resources(

            session["access_key"],

            session["secret_key"],

            session["region"]

        )



        answer = chat_with_ai(

            question,

            cost_data,

            resources

        )



        return jsonify({

            "reply": answer

        })



    except Exception as e:


        return jsonify({

            "reply":

            f"AI Assistant Error: {str(e)}"

        }),500


@app.route("/health")
def health():


    return jsonify({

        "application":

        "AI Cloud Cost Detective",


        "version":

        "V2.1",


        "status":

        "running"

    })


@app.route("/logout")
def logout():


    session.clear()


    return redirect("/")


@app.errorhandler(404)
def page_not_found(error):


    return jsonify({

        "error":

        "Page not found"

    }),404




@app.errorhandler(500)
def internal_server_error(error):


    return jsonify({

        "error":

        "Internal server error"

    }),500


if __name__ == "__main__":


    app.run(

        host="0.0.0.0",

        port=5000,

        debug=os.getenv("FLASK_DEBUG", "False").lower() == "true"

    )

