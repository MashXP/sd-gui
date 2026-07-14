import os
import signal
import subprocess
import threading
import queue

class ProcessRunner:
    def __init__(self, log_queue):
        self.process = None
        self.log_queue = log_queue
        self.is_running = False

    def start(self, cmd, cwd):
        """Launches the process in a background thread."""
        self.is_running = True
        threading.Thread(target=self._run_subprocess, args=(cmd, cwd), daemon=True).start()

    def _run_subprocess(self, cmd, cwd):
        try:
            self.process = subprocess.Popen(
                cmd,
                stdout=subprocess.PIPE,
                stderr=subprocess.STDOUT,
                text=True,
                bufsize=1,
                cwd=cwd,
                preexec_fn=os.setsid
            )
            
            for line in iter(self.process.stdout.readline, ''):
                self.log_queue.put(line)
            self.process.stdout.close()
            
            status = self.process.wait()
            self.log_queue.put(f"\n🛑 Process exited with code {status}\n")
        except Exception as e:
            self.log_queue.put(f"\n❌ Error starting process: {str(e)}\n")
        finally:
            self.is_running = False
            self.log_queue.put("__PROCESS_DONE__")

    def stop(self):
        """Interrupts the active subprocess group using SIGINT."""
        if not self.is_running or not self.process:
            return
            
        self.log_queue.put("\n⚠️ Stopping process group...\n")
        try:
            os.killpg(os.getpgid(self.process.pid), signal.SIGINT)
        except Exception as e:
            try:
                self.process.terminate()
            except Exception as ex:
                self.log_queue.put(f"❌ Failed to stop: {str(ex)}\n")

    def kill_force(self):
        """Forcefully kills the subprocess group (SIGKILL) on close."""
        if self.process:
            try:
                os.killpg(os.getpgid(self.process.pid), signal.SIGKILL)
            except Exception:
                pass
