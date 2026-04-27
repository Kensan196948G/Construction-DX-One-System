from django.http import FileResponse
from rest_framework import status
from rest_framework.decorators import api_view
from rest_framework.response import Response

from .models import Audit, Finding
from .report_generator import generate_audit_excel, generate_audit_pdf
from .serializers import AuditSerializer, FindingSerializer


@api_view(["GET", "POST"])
def audit_list(request):
    if request.method == "GET":
        audits = Audit.objects.all()
        status_filter = request.query_params.get("status")
        if status_filter:
            audits = audits.filter(status=status_filter)
        serializer = AuditSerializer(audits, many=True)
        return Response(serializer.data)

    serializer = AuditSerializer(data=request.data)
    if serializer.is_valid():
        serializer.save()
        return Response(serializer.data, status=status.HTTP_201_CREATED)
    return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


@api_view(["GET", "PUT", "DELETE"])
def audit_detail(request, pk):
    try:
        audit = Audit.objects.get(pk=pk)
    except Audit.DoesNotExist:
        return Response(status=status.HTTP_404_NOT_FOUND)

    if request.method == "GET":
        return Response(AuditSerializer(audit).data)

    if request.method == "PUT":
        serializer = AuditSerializer(audit, data=request.data)
        if serializer.is_valid():
            serializer.save()
            return Response(serializer.data)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

    audit.delete()
    return Response(status=status.HTTP_204_NO_CONTENT)


@api_view(["GET", "POST"])
def finding_list(request, audit_pk):
    try:
        audit = Audit.objects.get(pk=audit_pk)
    except Audit.DoesNotExist:
        return Response(status=status.HTTP_404_NOT_FOUND)

    if request.method == "GET":
        findings = audit.findings.all()
        severity_filter = request.query_params.get("severity")
        if severity_filter:
            findings = findings.filter(severity=severity_filter)
        serializer = FindingSerializer(findings, many=True)
        return Response(serializer.data)

    data = request.data.copy()
    data["audit"] = str(audit.id)
    serializer = FindingSerializer(data=data)
    if serializer.is_valid():
        serializer.save()
        return Response(serializer.data, status=status.HTTP_201_CREATED)
    return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


@api_view(["GET", "PUT", "DELETE"])
def finding_detail(request, audit_pk, pk):
    try:
        finding = Finding.objects.get(pk=pk, audit__id=audit_pk)
    except Finding.DoesNotExist:
        return Response(status=status.HTTP_404_NOT_FOUND)

    if request.method == "GET":
        return Response(FindingSerializer(finding).data)

    if request.method == "PUT":
        serializer = FindingSerializer(finding, data=request.data)
        if serializer.is_valid():
            serializer.save()
            return Response(serializer.data)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

    finding.delete()
    return Response(status=status.HTTP_204_NO_CONTENT)


@api_view(["GET"])
def audit_report_excel(request, pk):
    try:
        audit = Audit.objects.get(pk=pk)
    except Audit.DoesNotExist:
        return Response(status=status.HTTP_404_NOT_FOUND)

    findings = audit.findings.all()
    excel_file = generate_audit_excel(audit, findings)
    filename = f"audit_report_{audit.title.replace(' ', '_')}.xlsx"
    return FileResponse(
        excel_file,
        as_attachment=True,
        filename=filename,
        content_type="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
    )


@api_view(["GET"])
def audit_report_pdf(request, pk):
    try:
        audit = Audit.objects.get(pk=pk)
    except Audit.DoesNotExist:
        return Response(status=status.HTTP_404_NOT_FOUND)

    findings = audit.findings.all()
    pdf_file = generate_audit_pdf(audit, findings)
    filename = f"audit_report_{audit.title.replace(' ', '_')}.pdf"
    return FileResponse(
        pdf_file,
        as_attachment=True,
        filename=filename,
        content_type="application/pdf",
    )
