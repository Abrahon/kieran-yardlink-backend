# =========================
# GET BUSINESS PROFILE
# =========================

def get_business_profile(user):
    """
    Always returns BusinessProfile for landscaper user
    """
    return getattr(user, "landscaper_profile", None)