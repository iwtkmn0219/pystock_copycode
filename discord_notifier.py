import discord
import asyncio
import pyupbit
import time
from datetime import datetime, timedelta

# 업비트 로그인
f = open("./upbit.txt")
lines = f.readlines()
access = lines[0].strip()
secret = lines[1].strip()
token = lines[2].strip()
f.close()
my_upbit = pyupbit.Upbit(access, secret)

# discord bot token
DISCORD_TOKEN = token
# discord channel id (일반)
CHANNEL_ID = 1137546202708185182

# 디스코드 접근
intents = discord.Intents.default()
intents.typing = False
intents.presences = False
client = discord.Client(intents=intents)


# 메시지 전송
async def send_message(msg: str):
    channel = client.get_channel(CHANNEL_ID)
    if channel:
        await channel.send(msg)
    else:
        print("Cannot found channel")


# 특정 시간에 메시지를 전송한다.
async def send_message_at():
    current_time = datetime.now()
    if current_time.hour == 9 and current_time.minute == 0:
        total_assets = 0
        for dic in my_upbit.get_balances():
            if dic['currency'] == "KRW":
                total_assets += float(dic['balance'])
                continue
            current_price = pyupbit.get_current_price(f"KRW-{dic['currency']}")
            total_assets += current_price * float(dic['locked'])
            time.sleep(0.2)

        task = asyncio.create_task(send_message(f"{current_time.year}년 {current_time.month}월 {current_time.day}일: 현재 보유 KRW는 {format(round(total_assets), ',')}원 입니다."))
        await task
    await asyncio.sleep(59)


@client.event
async def on_ready():
    print(f"Success Login (로그인 정보: {client.user})")
    while True:
        task = asyncio.create_task(send_message_at())
        await task


@client.event
async def on_diconnect():
    print(f"{client.user}의 연결이 끊어졌습니다.")


client.run(DISCORD_TOKEN)
