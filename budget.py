import os


def get_budget_status(current_cost, monthly_budget=None):


    current_cost = float(current_cost)



    if monthly_budget is None:


        monthly_budget = os.getenv(

            "AWS_MONTHLY_BUDGET"

        )

    if not monthly_budget:


        return {


            "budget": 0,

            "spent": round(current_cost, 2),

            "remaining": 0,

            "used_percent": 0,

            "status": "Not Configured",

            "color": "gray"

        }
    try:
        monthly_budget = float(monthly_budget)
    except (ValueError, TypeError):
        return {
            "budget": 0,
            "spent": round(current_cost, 2),
            "remaining": 0,
            "used_percent": 0,
            "status": "Invalid Budget",
            "color": "red"
    }


    used_percent = (

        (current_cost / monthly_budget) * 100

        if monthly_budget > 0

        else 0

    )



    remaining = max(

        monthly_budget - current_cost,

        0

    )



    if used_percent >= 100:


        status = "Over Budget"

        color = "red"



    elif used_percent >= 80:


        status = "Warning"

        color = "orange"



    else:


        status = "Healthy"

        color = "green"



    return {


        "budget": round(monthly_budget, 2),


        "spent": round(current_cost, 2),


        "remaining": round(remaining, 2),


        "used_percent": round(used_percent, 1),


        "status": status,


        "color": color

    }

