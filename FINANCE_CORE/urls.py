from django.urls import include, path

from swagger_config import schema_view

urlpatterns = [
    path("api/authorizer/", include("authorizer.urls")),
    path("api/bills/", include("bills.urls")),
    path(
        "swagger/",
        schema_view.with_ui("swagger", cache_timeout=0),
        name="schema-swagger-ui",
    ),
    path("redoc/", schema_view.with_ui("redoc", cache_timeout=0), name="schema-redoc"),
]
