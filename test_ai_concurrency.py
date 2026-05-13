#!/usr/bin/env python3
import app_server


def main():
    original_provider = app_server.AI_PROVIDER
    original_wait = app_server.AI_QUEUE_WAIT_SECONDS
    app_server.AI_PROVIDER = "codex"
    app_server.AI_QUEUE_WAIT_SECONDS = 0
    acquired = app_server.AI_SEMAPHORE.acquire(blocking=False)
    if not acquired:
        raise AssertionError("No se pudo preparar el semáforo de IA para la prueba")
    try:
        try:
            app_server.call_ai(app_server.AGENT_INSTRUCTIONS, "{}")
        except app_server.AiBusyError:
            print("ok")
            return 0
        raise AssertionError("call_ai debería devolver AiBusyError cuando no hay concurrencia disponible")
    finally:
        app_server.AI_PROVIDER = original_provider
        app_server.AI_QUEUE_WAIT_SECONDS = original_wait
        app_server.AI_SEMAPHORE.release()


if __name__ == "__main__":
    raise SystemExit(main())
