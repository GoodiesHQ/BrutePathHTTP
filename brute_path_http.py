#!/usr/bin/env python3
from argparse import ArgumentParser
import aiohttp
import asyncio
import contextlib
import functools
import itertools
import signal
import sys

try:
    import uvloop
    asyncio.set_event_loop_policy(uvloop.EventLoopPolicy())
except ImportError:
    pass  # running without uvloop

try:
    import colorama
    C_RED = colorama.Style.BRIGHT + colorama.Fore.RED
    C_GRN = colorama.Style.BRIGHT + colorama.Fore.GREEN
    C_CYN = colorama.Style.BRIGHT + colorama.Fore.CYAN
    C_RST = colorama.Style.RESET_ALL
    colorama.init()
    def cprint(color, *args, **kwargs):
        f = kwargs.get("file", sys.stdout)
        print(color, end="", flush=True, file=f)
        print(*args, **kwargs)
        print(C_RST, end="", flush=True, file=f)
except ImportError:
    C_RED = C_GRN = C_CYN = C_RST = None
    def cprint(color, *args, **kwargs):
        print(*args, **kwargs)


USERAGENT = "Mozilla/5.0 (Windows NT 6.1; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/40.0.2214.85 Safari/537.36"
HEADERS = {"User-Agent": USERAGENT}
VERBOSE = False

def as_completed(tasks, worker_cnt):
    futs = [asyncio.ensure_future(t) for t in itertools.islice(tasks, 0, worker_cnt)]

    async def wrapped():
        await asyncio.sleep(0)
        for fut in futs:
            if fut.done():
                futs.remove(fut)
                with contextlib.suppress(StopIteration):
                    futs.append(asyncio.ensure_future(next(tasks)))
                return fut.result()

    while len(futs):
        yield wrapped()

async def check_url(url, timeout, status_codes, fout):
    try:
        async with aiohttp.ClientSession() as session:
            async with session.get(url, headers=HEADERS, timeout=timeout) as resp:
                if resp.status in status_codes:
                    cprint(C_GRN, "[+] Found", end=": ")
                    print(url)
                    print(url, file=fout)
                else:
                    if VERBOSE:
                        cprint(C_RED, "[-] Not Found", end=": ")
                        print(url)
    except Exception as e:
        print(e, file=sys.stderr)


async def run(http_dir: str, words: list, extensions: list, status_codes: list, output: str, conns: int, timeout: int):
    extensions = set(extensions) or {""}

    with open(output, "a+") as fout:
        tasks = (check_url(http_dir + word + ("." + ext if ext else ""), timeout, status_codes, fout) \
                for word in words for ext in extensions)
        for task in as_completed(tasks, conns):
            await task

def shutdown(loop):
    cprint(C_CYN, "\nShutting down...")
    loop.stop()
    tasks = asyncio.Task.all_tasks()
    for i, task in enumerate(tasks):
        task._log_destroy_pending = False
        task.cancel()
    with contextlib.suppress(RuntimeError):
        loop.close()

def main():
    ap = ArgumentParser()
    ap.add_argument("--dir", "-d", type=str, required=True, help="Full path to HTTP directory")
    ap.add_argument("--wordlist", "-w", type=str, required=True, help="File containing words to try")
    ap.add_argument("--ext", "-e", type=str, nargs="+", default=[], help="List of extensions to attempt")
    ap.add_argument("--status", "-s", type=int, nargs="+", default=[200], help="Status codes to accept")
    ap.add_argument("--output", "-o", type=str, default="output.txt", help="Output file to store discovered URLs")
    ap.add_argument("--conns", "-c", type=int, default=100, help="Number of concurrent connections")
    ap.add_argument("--timeout", "-t", type=int, default=10, help="Connection timeout")
    ap.add_argument("--verbose", "-v", action="store_true", help="Verbose output")
    args = ap.parse_args()

    global VERBOSE
    VERBOSE = args.verbose

    try:
        with open(args.wordlist, "r") as fin:
            words = [line.strip() for line in fin.readlines() if " " not in line]
        cprint(C_GRN, "[+]", end=" ", flush=True)
        print("Loaded {} words from '{}'.".format(len(words), args.wordlist))
    except OSError:
        cprint(C_RED, "[!]", end=" ", flush=True)
        print("Could not read '{}'".format(args.wordlist))
        sys.exit(1)

    http_dir = args.dir.rstrip("/") + "/"
    loop = asyncio.get_event_loop()

    try:
        loop.add_signal_handler(signal.SIGINT, functools.partial(shutdown, loop))
        loop.run_until_complete(run(http_dir, words, args.ext, args.status, args.output, args.conns, args.timeout))
    except (RuntimeError, asyncio.CancelledError, KeyboardInterrupt) as e:
        print(e)
        pass

if __name__ == "__main__":
    main()
