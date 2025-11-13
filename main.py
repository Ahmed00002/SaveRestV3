# Copyright (c) 2025 devgagan : https://github.com/devgaganin.
# Licensed under the GNU General Public License v3.0.
# See LICENSE file in the repository root for full license text.

import asyncio
import importlib
import os
import sys

from shared_client import start_client, client, app, userbot


async def load_and_run_plugins():
    """
    plugins ফোল্ডারের সব .py ফাইল import করবে,
    আর চাইলে run_<plugin>_plugin() নামের extra async hook থাকলে সেটা চালাবে।
    NOTE: এখানে আর start_client() নেই, main() এ একবারই কল হবে।
    """
    plugin_dir = "plugins"
    plugins = [
        f[:-3]
        for f in os.listdir(plugin_dir)
        if f.endswith(".py") and f != "__init__.py"
    ]

    for plugin in plugins:
        try:
            module = importlib.import_module(f"plugins.{plugin}")
            print(f"✅ Loaded plugin: {plugin}")

            hook_name = f"run_{plugin}_plugin"
            if hasattr(module, hook_name):
                hook = getattr(module, hook_name)
                print(f"🚀 Running hook for plugin: {plugin}")
                if asyncio.iscoroutinefunction(hook):
                    await hook()
                else:
                    hook()
        except Exception as e:
            print(f"❌ Failed to load plugin {plugin}: {e}")


async def main():
    print("Starting clients ...")

    # 1️⃣ Telethon + Pyrogram clients start
    await start_client()

    # 2️⃣ Plugins/handlers load
    await load_and_run_plugins()
    print("All plugins loaded. Bot is running ✅")

    # 3️⃣ পুরোনো স্টাইলে infinite loop, যাতে bot alive থাকে
    try:
        while True:
            await asyncio.sleep(1)
    except asyncio.CancelledError:
        # asyncio.run cancel করলে এখান দিয়ে বের হবে
        pass
    finally:
        # 4️⃣ Graceful shutdown: loop বন্ধের আগে সব client থামিয়ে দাও
        print("Shutting down ...")
        try:
            await app.stop()
        except Exception:
            pass

        try:
            await userbot.stop()
        except Exception:
            pass

        try:
            await client.disconnect()
        except Exception:
            pass


if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        print("Interrupted by user, exiting...")
        sys.exit(0)
