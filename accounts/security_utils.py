# accounts/security_utils.py

def get_client_ip(request):
    """
    Handles reverse proxies/CDNs when configured properly.
    If you use Nginx/Cloudflare, ensure the correct header is forwarded.
    """
    xff = request.META.get("HTTP_X_FORWARDED_FOR")
    if xff:
        # first IP is original client in most setups
        return xff.split(",")[0].strip()
    return request.META.get("REMOTE_ADDR")


def parse_device(user_agent: str | None):
    """
    Lightweight parsing without extra dependencies.
    If you want richer parsing later, install 'user-agents'.
    """
    if not user_agent:
        return {"device_type": None, "os": None, "browser": None}

    ua = user_agent.lower()

    device_type = "desktop"
    if "mobile" in ua or "android" in ua or "iphone" in ua:
        device_type = "mobile"
    if "ipad" in ua or "tablet" in ua:
        device_type = "tablet"

    os = None
    if "android" in ua:
        os = "Android"
    elif "iphone" in ua or "ios" in ua or "ipad" in ua:
        os = "iOS"
    elif "windows" in ua:
        os = "Windows"
    elif "mac os" in ua or "macintosh" in ua:
        os = "macOS"
    elif "linux" in ua:
        os = "Linux"

    browser = None
    if "chrome" in ua and "edg" not in ua:
        browser = "Chrome"
    elif "safari" in ua and "chrome" not in ua:
        browser = "Safari"
    elif "firefox" in ua:
        browser = "Firefox"
    elif "edg" in ua:
        browser = "Edge"

    return {"device_type": device_type, "os": os, "browser": browser}