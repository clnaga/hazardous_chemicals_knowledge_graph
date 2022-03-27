import asyncio
import websockets
from neo4j import GraphDatabase
import json

async def echo(websocket, path):
    async for message in websocket:
        uri = "neo4j://localhost:7687"
        driver = GraphDatabase.driver(uri, auth=("neo4j", "123456"), max_connection_lifetime=1000)
        
        data = {
            '危险品': 0, '索引': 1, '侵入途径': 2, '健康危害': 3, '环境危害': 4,
            '皮肤接触': 5, '眼睛接触': 6, '吸入': 7, '食入': 8, '有害燃烧产物': 9,
            '灭火方法': 10, '灭火注意事项及措施': 11, '应急行动': 12, '操作注意事项': 13,
            '储存注意事项': 14, '禁配物': 15, '避免接触条件': 16, '风险事件': 17, '风险产物': 18
        }
        # 获取危险化学品信息
        wxp_xz = {}
        wxp_jd = []
        wxp_gx = []

        def get_node_xz(tx, name):
            # 获取危险化学品性质
            for n, label in tx.run("match (n:危险品) where n.name=$name return n, labels(n)", name=name):
                res_keys = list(n)
                for i in range(len(res_keys)):
                    wxp_xz[res_keys[i]] = dict(n)[res_keys[i]]
            # 获取危险化学品节点和关系
            for name, id, label in tx.run("match (n:危险品) where n.name=$name return n.name, id(n), labels(n)", name=name):
                res = {}
                res["id"] = str(id)
                res["category"] = str(data[label[0]])
                res["name"] = str(id)
                res["label"] = name
                res["symbolSize"] = 60
                wxp_jd.append(res)
            for b_name, b_id, b_label, r_type, r_startId, r_endId in tx.run("match (n:危险品)-[r]->(b) where n.name=$name return b.name, id(b), labels(b), type(r), id(startNode(r)), id(endNode(r))", name=name):
                b_res = {}
                b_res["id"] = str(b_id)
                b_res["category"] = str(data[b_label[0]])
                b_res["name"] = str(b_id)
                b_res["label"] = b_name
                b_res["symbolSize"] = 40
                wxp_jd.append(b_res)

                r_res = {}
                r_res["source"] = str(r_startId)
                r_res["target"] = str(r_endId)
                r_res["value"] = r_type
                wxp_gx.append(r_res) 

        with driver.session() as session:
            session.read_transaction(get_node_xz, message)
            
        driver.close()

        msg = {}
        msg['wxp_xz'] = wxp_xz
        msg['wxp_jd'] = wxp_jd
        msg['wxp_gx'] = wxp_gx
        print("successd!")
        await websocket.send(json.dumps(msg, ensure_ascii=False))

asyncio.get_event_loop().run_until_complete(websockets.serve(echo, 'localhost', 2333))
asyncio.get_event_loop().run_forever()