from dotenv import load_dotenv
from livekit.agents import cli, WorkerOptions, JobContext
from livekit_handler import get_agent_en

load_dotenv()


async def entrypoint(ctx: JobContext):
    await ctx.connect()

    room_name = ctx.room.name  # ✅ KEY FIX

    session, assistant = get_agent_en(room_name)

    await session.start(room=ctx.room, agent=assistant)

    await session.say("Hello! How can I help you today?")

    import asyncio
    while True:
        await asyncio.sleep(1)


if __name__ == "__main__":
    cli.run_app(
        WorkerOptions(
            entrypoint_fnc=entrypoint,
            agent_name="booking-voice-en",
            port=8082
        )
    )