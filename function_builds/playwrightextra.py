# this is the connect method of the PipeTransport class in adamhale\.local\lib\python3.10\site-packages\playwright\_impl\_transport.py

async def connect(self) -> None:
    self._stopped_future: asyncio.Future = asyncio.Future()

    try:
        # For pyinstaller
        env = get_driver_env()
        if getattr(sys, "frozen", False):
            env.setdefault("PLAYWRIGHT_BROWSERS_PATH", "0")

        startupinfo = None
        if sys.platform == "win32":
            startupinfo = subprocess.STARTUPINFO()
            startupinfo.dwFlags |= subprocess.STARTF_USESHOWWINDOW
            startupinfo.wShowWindow = subprocess.SW_HIDE

        executable_path, entrypoint_path = compute_driver_executable()
        self._proc = await asyncio.create_subprocess_exec(
            executable_path,
            entrypoint_path,
            "run-driver",
            stdin=asyncio.subprocess.PIPE,
            stdout=asyncio.subprocess.PIPE,
            stderr=_get_stderr_fileno(),
            limit=32768,
            env=env,
            startupinfo=startupinfo,
        )
    except Exception as exc:
        self.on_error_future.set_exception(exc)
        raise exc

    self._output = self._proc.stdin
