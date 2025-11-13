# Copyright (c) 2025 devgagan : https://github.com/devgaganin.  
# Licensed under the GNU General Public License v3.0.  
# See LICENSE file in the repository root for full license text.






import asyncio
import importlib
import os
import sys

from pyrogram import idle
from shared_client import start_client, client, app, userbot


# async def load_and_run_plugins():
#     await start_client()
#     plugin_dir = "plugins"
#     plugins = [f[:-3] for f in os.listdir(plugin_dir) if f.endswith(".py") and f != "__init__.py"]

#     for plugin in plugins:
#         module = importlib.import_module(f"plugins.{plugin}")
#         if hasattr(module, f"run_{plugin}_plugin"):
#             print(f"Running {plugin} plugin...")
#             await getattr(module, f"run_{plugin}_plugin")()  

# updated plugin function
async def load_and_run_plugins():
    """
    plugins ফোল্ডারের সব .py ফাইল import করবে,
    আর চাইলে run_<plugin>_plugin() নামের extra async hook থাকলে সেটা চালাবে।
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

            # Optional hook: run_<plugin>_plugin()
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


# async def main():
#     await load_and_run_plugins()
#     while True:
#         await asyncio.sleep(1)  

# if __name__ == "__main__":
#     loop = asyncio.get_event_loop()
#     print("Starting clients ...")
#     try:
#         loop.run_until_complete(main())
#     except KeyboardInterrupt:
#         print("Shutting down...")
#     except Exception as e:
#         print(e)
#         sys.exit(1)
#     finally:
#         try:
#             loop.close()
#         except Exception:
#             pass

async def main():
    print("Starting clients ...")

    # 1️⃣ Telethon + Pyrogram clients start
    await start_client()

    # 2️⃣ Plugins/handlers load
    print("Loading plugins ...")
    await load_and_run_plugins()
    print("All plugins loaded. Bot is up and running ✅")

    # 3️⃣ Bot কে alive রাখো, যেন commands/process সব handle করতে পারে
    await idle()

    # 4️⃣ Graceful shutdown
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