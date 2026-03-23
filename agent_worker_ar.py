from dotenv import load_dotenv
from livekit.agents import cli, WorkerOptions, JobContext
from livekit_handler import get_agent_ar

load_dotenv()


async def entrypoint(ctx: JobContext):
    await ctx.connect()

    session, assistant = get_agent_ar()
    await session.start(room=ctx.room, agent=assistant)

    await session.say("أهلاً وسهلاً! تحب أساعدك ازاي؟")

    import asyncio
    while True:
        await asyncio.sleep(1)


if __name__ == "__main__":
    cli.run_app(
        WorkerOptions(
            entrypoint_fnc=entrypoint,
            agent_name="booking-voice-ar",
            port=8081  # 🔥 explicit
        )
    )