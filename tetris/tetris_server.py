from asyncio import start_server
import websockets, json
import asyncio
import numpy as np
from random import randint

global ALL_SOCKET, SOCKET_AUTOINCRE
ALL_SOCKET = []
ALL_SOCKET_IDX = []
SOCKET_AUTOINCRE = 0

#게이머와 소켓 서버가 서로 연결될 때 accept 실행
async def accept(websocket, path):
    global SOCKET_AUTOINCRE, ALL_SOCKET, ALL_SOCKET_IDX
    print("connected from client")
    websocket.idx = SOCKET_AUTOINCRE 
    SOCKET_AUTOINCRE += 1
    websocket.connected = True
    websocket.isReady = False
    ALL_SOCKET.append(websocket)
    ALL_SOCKET_IDX.append(websocket.idx)
    
    #게이머에게 아이디값 보내주기
    data = {"code" : "my_socket_idx", "socket_idx" : websocket.idx}
    await websocket.send(json.dumps(data));#json변수를 문자열로 바꾸어 준다
    
    #전체 소켓을 보내준다. 사용자의 정보
    await sendingAllSocketInfo()
    
    while True:
        try:
            data = await websocket.recv()
            data = json.loads(data) #다시 json으로 바꾸기 배열로 들어온다
            
            if data["code"] == "iam_ready":
                #레디 선언한 소켓에 그 상태값, 즉 isready값을 true로 바꿔주기
                findIdxFromAllSocket(data["socket_idx"]).isReady = True
                
                #전체에게 한 친구가 레디상태임을 알려준다
                for sc in ALL_SOCKET:
                    if sc.idx != data["socket_idx"]: #자기 자신에게는 알리지 않아도 된다
                        data = {"code": "friend_ready", "socket_idx":data["socket_idx"]}
                        await sc.sc.send(json.dumps(data)) #동기형
                
                isAllReady = True
                for sc in ALL_SOCKET:
                    if sc.isReady != True:
                        isAllReady = False
                
                if isAllReady == True: #전체가 레디인 상태
                    await standby()
                
                
        except websocket.ConnectionClosed: #소켓 연결이 끊긴 경우
            websocket.connected = False
            continue#에러가 있어도 게속 실행
        finally:
            if websocket.connected != True: #연결 끊김
                for idx, val in enumerate(ALL_SOCKET_IDX):
                    if val == websocket.idx:
                        del ALL_SOCKET_IDX[idx]
                del ALL_SOCKET[websocket.idx]
                break

async def standby():
    print("standby")


    global NEXT_BLOCK_SHAPE, NOW_BLOCK_SHAPE, ALL_BLOCK, BLOCK_POSITION_SHAPE, BLOCK_ARRAY
    NEXT_BLOCK_SHAPE = "" #다음 블록
    NOW_BLOCK_SHAPE = "" #현재 블록
    ALL_BLOCK = []
    BLOCK_ARRAY = []
    
    ALL_BLOCK.append(np.array([
        ["0:0", "1:0", "2:0", "3:0"],
        ["0:0", "0:1", "0:2", "0:3"],
      ]))
    ALL_BLOCK.append(np.array([
        ["0:0", "0:1", "1:1"],
        ["0:1", "0:0", "1:0"],
        ["0:0", "1:0", "1:1"],
        ["1:0", "0:1", "1:1"],
      ]))
    ALL_BLOCK.append(np.array([
        ["0:1", "1:1", "1:0"],
        ["0:-1", "0:0", "1:0"],
        ["0:1", "0:0", "1:0"],
        ["0:-1", "1:-1", "1:0"],
      ]))
    ALL_BLOCK.append(np.array([
        ["0:1", "1:1", "2:1", "0:0"],
        ["0:1", "0:0", "0:-1", "1:-1"],
        ["0:-2", "1:-2", "2:-2", "2:-1"],
        ["0:0", "0:1", "-1:2", "0:2"],
      ]))
    ALL_BLOCK.append(np.array([
        ["0:1", "1:1", "2:1", "2:0"],
        ["1:-1", "1:0", "1:1", "2:1"],
        ["-1:1", "-1:0", "0:0", "1:0"],
        ["0:-1", "1:-1", "1:0", "1:1"],
      ]))
    ALL_BLOCK.append(np.array([["1:1", "2:1", "1:0", "2:0"]]))
       
async def newBlock():
    global NEXT_BLOCK_SHAPE, NOW_BLOCK_SHAPE, ALL_BLOCK, BLOCK_POSITION_SHAPE
    BLOCK_POSITION_SHAPE = 0

    if NEXT_BLOCK_SHAPE != "":
        BLOCK_ARRAY.append(randint(0, ALL_BLOCK.length -1))
        BLOCK_ARRAY.append(randint(0, ALL_BLOCK.length -1))
        
        NOW_BLOCK_SHAPE = BLOCK_ARRAY[len(BLOCK_ARRAY)-2]
        NEXT_BLOCK_SHAPE = BLOCK_ARRAY[len(BLOCK_ARRAY)-1]
    else :
        BLOCK_ARRAY.append(randint(0, ALL_BLOCK.length -1))
        NOW_BLOCK_SHAPE = NEXT_BLOCK_SHAPE
        NEXT_BLOCK_SHAPE = BLOCK_ARRAY[len(BLOCK_ARRAY)-1]
        
    data = {"code":"newblock", "next_block":NEXT_BLOCK_SHAPE, "now_block":NOW_BLOCK_SHAPE}
    data = json.dumps(data)
    
    for sc in ALL_SOCKET:
        await sc.send(data)
        
        
        
def findIdxFromAllSocket(idx): #인덱스로 실제 웹소켓 객체를 보내주기
    for sc in ALL_SOCKET:
        if sc.idx == idx:
            return sc

#전체 플레이어에게 아이디 인덱스를 보내는 함수    
async def sendingAllSocketInfo():
     data = {"code" : "all_friends", "sockets" : ALL_SOCKET_IDX}
     for sc in ALL_SOCKET:
         await sc.send(json.dumps(data))
         print("sendingAllSocketInfo!")

#웹소켓서버가 localhost 8080 포트에 생성
#8080포트에 웹소켓이 상시 대기를 해서 데이터가 들어오면 캡쳐한다.
#비동기형태로 실행이 되는데, 동기처리를 하면 동시에 데이터 들어오면 처리하기가 힘들다.
start_server = websockets.serve(accept, "localhost", 8080)
loop = asyncio.get_event_loop()#러닝 이벤트 루프를 리턴해줌
loop.run_until_complete(start_server)#함수가 끝날때까지 이벤트 루프를 실행함

try:
    loop.run_forever()#이벤트 루프를 돌려줌
finally:
    loop.close()#메모리 누수를 방지


    
