from drf_yasg import openapi
from drf_yasg.views import get_schema_view

schema_view = get_schema_view(
    openapi.Info(
        title="FINE_FINANCE_CORE",
        default_version="v1",
        description="bills finance core API",
        terms_of_service="",
        contact=openapi.Contact(email="viniciuscoelhonau975@gmail.com"),
        license=openapi.License(name=""),
    ),
    public=True,
)
