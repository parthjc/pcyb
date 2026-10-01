using System;
using System.IO;
using System.ServiceProcess;

public sealed class ZYNTRASECWatchdogService : ServiceBase
{
    private const string SERVICE_NAME = "ZYNTRASECWatchdog";
    private readonly string root =
        Path.Combine(Environment.GetFolderPath(Environment.SpecialFolder.CommonApplicationData),
        "ZYNTRASEC", "System");
    private readonly string logPath;

    public ZYNTRASECWatchdogService()
    {
        ServiceName = SERVICE_NAME;
        CanStop = true;
        CanPauseAndContinue = false;
        CanShutdown = false;
        AutoLog = false;
        logPath = Path.Combine(root, "native_service.log");
    }

    protected override void OnStart(string[] args)
    {
        // Keep OnStart intentionally minimal. Windows SCM must receive
        // SERVICE_RUNNING immediately; no child process, timer, or PowerShell
        // work is performed from Session 0.
        Directory.CreateDirectory(root);
        Log("SERVICE_ONSTART");
    }

    protected override void OnStop()
    {
        Log("SERVICE_ONSTOP");
    }

    private void Log(string message)
    {
        try
        {
            Directory.CreateDirectory(root);
            File.AppendAllText(logPath,
                DateTime.Now.ToString("yyyy-MM-dd HH:mm:ss ") +
                message + Environment.NewLine);
        }
        catch { }
    }

    public static void Main()
    {
        ServiceBase.Run(new ZYNTRASECWatchdogService());
    }
}
