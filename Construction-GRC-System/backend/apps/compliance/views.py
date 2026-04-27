from __future__ import annotations

from rest_framework import status
from rest_framework.decorators import api_view
from rest_framework.response import Response

from .models import Control
from .nist_mapping import get_nist_compliance_heatmap, get_nist_framework_status
from .serializers import ControlSerializer
from .soa_generator import generate_soa, generate_soa_report


@api_view(["GET", "POST"])
def control_list(request):
    if request.method == "GET":
        controls = Control.objects.all()
        status_filter = request.query_params.get("implementation_status")
        if status_filter:
            controls = controls.filter(implementation_status=status_filter)
        applicability_filter = request.query_params.get("applicability")
        if applicability_filter:
            controls = controls.filter(applicability=applicability_filter)
        serializer = ControlSerializer(controls, many=True)
        return Response(serializer.data)

    serializer = ControlSerializer(data=request.data)
    if serializer.is_valid():
        serializer.save()
        return Response(serializer.data, status=status.HTTP_201_CREATED)
    return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


@api_view(["GET", "PUT", "DELETE"])
def control_detail(request, pk):
    try:
        control = Control.objects.get(pk=pk)
    except Control.DoesNotExist:
        return Response(status=status.HTTP_404_NOT_FOUND)

    if request.method == "GET":
        return Response(ControlSerializer(control).data)

    if request.method == "PUT":
        serializer = ControlSerializer(control, data=request.data)
        if serializer.is_valid():
            serializer.save()
            return Response(serializer.data)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

    control.delete()
    return Response(status=status.HTTP_204_NO_CONTENT)


@api_view(["GET"])
def soa_list(request):
    controls = Control.objects.all()
    soa = generate_soa(controls)
    return Response(soa)


@api_view(["GET"])
def soa_download(request):
    controls = Control.objects.all()
    report = generate_soa_report(controls)
    response = Response(report)
    response["Content-Disposition"] = 'attachment; filename="soa_report.json"'
    response["Content-Type"] = "application/json"
    return response


@api_view(["GET"])
def nist_csf_status(request):
    controls = Control.objects.all()
    status_data = get_nist_framework_status(controls)
    return Response(status_data)


@api_view(["GET"])
def nist_csf_heatmap(request):
    controls = Control.objects.all()
    heatmap = get_nist_compliance_heatmap(controls)
    return Response(heatmap)


@api_view(["GET"])
def framework_compliance_rates(request):
    controls = Control.objects.all()

    soa = generate_soa(controls)
    nist = get_nist_framework_status(controls)

    iso_rate = soa["overall_compliance"]["compliance_rate"]
    nist_rate = (
        round(
            sum(f["implementation_score"] * f["total_controls"] for f in nist["functions"].values())
            / max(sum(f["total_controls"] for f in nist["functions"].values()), 1),
            1,
        )
        if nist["functions"]
        else 0.0
    )

    return Response(
        {
            "frameworks": [
                {
                    "framework": "ISO 27001:2022",
                    "compliance_rate": iso_rate,
                    "implemented_controls": soa["overall_compliance"]["implemented"],
                    "total_controls": soa["overall_compliance"]["total"],
                    "domain_breakdown": soa["compliance_summary"],
                },
                {
                    "framework": "NIST CSF 2.0",
                    "compliance_rate": nist_rate,
                    "total_functions": 6,
                    "function_breakdown": {
                        fname: {
                            "coverage_rate": fdata["coverage_rate"],
                            "implementation_score": fdata["implementation_score"],
                        }
                        for fname, fdata in nist["functions"].items()
                    },
                },
            ]
        }
    )
