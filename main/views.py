from django.shortcuts import render

def test_view(requst):
    return render(requst,'base.html',{})
