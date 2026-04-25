from rest_framework import status
from rest_framework.decorators import api_view
from rest_framework.response import Response

from .models import Control
from .serializers import ControlSerializer


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
