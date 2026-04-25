from rest_framework import status
from rest_framework.decorators import api_view
from rest_framework.response import Response

from .models import Risk
from .serializers import RiskSerializer


@api_view(["GET", "POST"])
def risk_list(request):
    if request.method == "GET":
        risks = Risk.objects.all()
        status_filter = request.query_params.get("status")
        if status_filter:
            risks = risks.filter(status=status_filter)
        serializer = RiskSerializer(risks, many=True)
        return Response(serializer.data)

    serializer = RiskSerializer(data=request.data)
    if serializer.is_valid():
        serializer.save()
        return Response(serializer.data, status=status.HTTP_201_CREATED)
    return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


@api_view(["GET", "PUT", "DELETE"])
def risk_detail(request, pk):
    try:
        risk = Risk.objects.get(pk=pk)
    except Risk.DoesNotExist:
        return Response(status=status.HTTP_404_NOT_FOUND)

    if request.method == "GET":
        return Response(RiskSerializer(risk).data)

    if request.method == "PUT":
        serializer = RiskSerializer(risk, data=request.data)
        if serializer.is_valid():
            serializer.save()
            return Response(serializer.data)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

    risk.delete()
    return Response(status=status.HTTP_204_NO_CONTENT)
