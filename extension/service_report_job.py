import unohelper
from com.sun.star.task import XJobExecutor

IMPLEMENTATION_NAME = "com.innse.servicereport.Job"


class ServiceReportJob(unohelper.Base, XJobExecutor):
    def __init__(self, ctx):
        self.ctx = ctx

    def trigger(self, command):
        from report_generator import main
        main.dispatch(self.ctx, command)


g_ImplementationHelper = unohelper.ImplementationHelper()
g_ImplementationHelper.addImplementation(
    ServiceReportJob, IMPLEMENTATION_NAME, (IMPLEMENTATION_NAME,))
