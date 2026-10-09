import json
import time

class Agentbreaker:
    def __init__(self, logger, composer, lmtester, evaluator, deployer):
        self.logger = logger
        self.composer = composer
        self.lmtester = lmtester
        self.evaluator = evaluator
        self.deployer = deployer


    def run(self, exp_num, exp_data):

        self.logger.exp_num = exp_num

        title = exp_data['title'] 
        elements = exp_data["elements"]
        usertask = exp_data['usertask']

        self.logger.info(f"\n🌐 [HTML {title}]")
        self.logger.info(f"▶️ User task: {repr(usertask)}", indent=1)
  
        # Result
        success = False
        ui_text = ""

        # strategy libraries
        removed_library = []
        efficient_library = []
        inefficient_library = []
        new_strategy = None
        
        start_time = time.time()
        for epoch in range(20):
            self.logger.epoch_num = epoch
            self.logger.info(f"\n🔁 Epoch {epoch+1}/{20}", indent=1)

            self.logger.log("a_strategy", f"""<removed>{json.dumps(removed_library, indent=2)}\n\n<new>{json.dumps(new_strategy, indent=2)}\n\n<efficient>{json.dumps(efficient_library, indent=2)}\n\n<inefficient>{json.dumps(inefficient_library, indent=2)}""")
            removed_library = []

            if epoch == 0:
                ui_text = self.composer.compose_without_strategy()
            else:
                ui_text = self.composer.compose(
                    user_goal=usertask,
                    html=elements,
                    efficient_strategy_library=[new_strategy] + efficient_library,
                    inefficient_strategy_library=inefficient_library,
                )

            self.logger.info(f"📊 attack payload: {repr(ui_text)}", indent=2)

            curr_rank, rank1_sentence, rank1_reason = self.lmtester.lmtest(
                ui_text=ui_text,
                html=elements,
                usertask=usertask
            )
            # Assess New Strategy's efficiency ##
                
            self.logger.info(f"📊 Curr Rank: {curr_rank}", indent=2)

            if new_strategy is not None:
                rank_delta = new_strategy["prev_rank"]  - curr_rank
                self.logger.info(f"📊 New Strategy Rank Delta: {str(rank_delta)}", indent=3)

                if rank_delta > 0:
                    efficient_library.append(new_strategy)
                elif rank_delta <= 0:
                    inefficient_library.append(new_strategy)

                new_strategy["rank_delta"] = rank_delta

            # Makeup New Strategy ##
            new_strategy = self.lmtester.makeup_new_strategy(usertask, elements, rank1_sentence, rank1_reason, existing_strategies=efficient_library + inefficient_library)
            new_strategy["prev_rank"] = curr_rank
            self.logger.info(f"📊 New Strategy Made: {new_strategy['content']}", indent=2)

            if curr_rank == 0:
                self.logger.info("🏆 Evaluation Start", indent=2)
                self.deployer.inject(ui_text, exp_num=exp_num)
                html_p = self.deployer.deploy()

                try:
                    success = self.evaluator.validate(usertask=usertask, exp_num=exp_num, epoch_num=epoch)
                finally:
                    html_p.kill()
                
                if success:
                    self.logger.info("📊 Evaluation Success", indent=3)
                    break
                else:
                    self.logger.info("📊 Evaluation Failed", indent=3)
                    removed_library = [d for d in efficient_library if abs(d["rank_delta"]) <= 1] + [d for d in inefficient_library if abs(d["rank_delta"]) <= 1]
                    efficient_library = [d for d in efficient_library if abs(d["rank_delta"]) > 1]
                    inefficient_library = [d for d in inefficient_library if abs(d["rank_delta"]) > 1]


        end_time = time.time()
        result_record = {
            "html_index": exp_num,
            "epochs_used": epoch + 1,
            "success": success,
            "ui_text": ui_text,
            "ui_text_length": len(ui_text),
            "optimization_time_sec": round(end_time - start_time, 3)
        }
        
        return result_record
