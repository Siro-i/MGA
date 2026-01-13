import json
import time
from maa.context import Context
from maa.custom_action import CustomAction
from maa.agent.agent_server import AgentServer
import UtilTools

@AgentServer.custom_action("StageSelect")
class StageSelect(CustomAction):
    def run(self, context: Context, argv: CustomAction.RunArg) -> bool:
            params = json.loads(argv.custom_action_param)
            target = params.get("stage_target")
            print("[StageSelect] stage_target:",target)
            
            if not target:
                print("[StageSelect] Error: 未指定 stage_target 参数")
              
            image=UtilTools.get_image(context)
            result=UtilTools.get_result(context,image,target=target)
            selection_result = list(result["all_results"])

            while selection_result:
                if context.tasker.running:
                    item = selection_result.pop(0) 
                    print("当前备选:",item["box"])
                    UtilTools.click_roi(context,item["box"])
                    time.sleep(0.6)
                    image=UtilTools.get_image(context)
                    result=UtilTools.get_result(context,image,target=target + "_OCR")
                    
                    if result["found"]:
                        print("匹配成功:",item)
                        return True
                    else:
                        print("匹配失败:",item)
                else:
                    context.tasker.post_stop().wait()
                    return False
            
            print("[StageSelect] 所有候选项均匹配失败")
            return False
                        
