from API.recommend import load_recommendation_data, router

@router.post("/reload", status_code=200)
def reload_offers():
    try:
        load_recommendation_data()
        return {"message": "Données rechargées avec succès"}
    except Exception as e:
        return {"error": str(e)}