# AgentBreaker: Evaluating Context-Aware Indirect Prompt Injection Risks in Modern Web Agents

## Artifact Description

LLM-powered web agents are already deployed at consumer scale. Despite their increasing use for web automation, their security implications under Indirect Prompt Injection (IPI) attacks remain largely understudied, while existing attack methods achieve relatively low attack success rates (ASRs).

**AgentBreaker** is an automated framework for generating context-aware indirect prompt injection attacks by composing adversarial phrases tailored to the HTML context of each target webpage.

This artifact consists of the following components:

<ol type="A">
  <li>Target HTML pages collected from Online-Mind2Web</li>
  <li>AgentBreaker source code</li>
  <li>Docker images for the target web agents</li>
  <li>Docker images and scripts for reproducing the experiments presented in the paper</li>
  <li>Sample results for attacks</li>
</ol>

We tested the artifact on a machine with the following configuration:

- 192 CPU cores
- 754 GB system memory
- 80 GB GPU VRAM
- Ubuntu 24.04 (64-bit)
- At least 100 GB of available disk space

This artifact is intended to reproduce the evaluation presented in Sections 5.2 and 6.1 of the paper, and to support the claims made in Table 1 and Table 3.

A single configuration (one agent, one action, one LLM in Demo version) for attack takes approximately **30 minutes**. Reproducing all results in **Table 1** (3 agents × 4 actions × 2 LLMs) takes approximately **12 hours** in total.

Defense evaluation takes longer; a single configuration takes approximately **10 hours**.

Please note that exact numerical results may differ due to the inherent nondeterminism of commercial LLM APIs and stochastic agent behavior.

# Getting Started

## Prerequisites
- Ubuntu 22.04+
- NVIDIA GPU (≥4 GB VRAM)
- NVIDIA driver **≥ 570.26** (CUDA 12.8+)
- NVIDIA Container Toolkit
- ≥100 GB available disk space
- ≥32 CPU cores
- ≥16 GB RAM
- `GPT_API_KEY` and `LLAMA_API_KEY`

**Note:** API keys will be provided to the artifact reviewers via a HotCRP comment.
Each API key includes up to **USD 50** in usage credits, which is sufficient to reproduce the experiments included in this artifact.

## Installation Instructions

The evaluation is performed using two separate Docker containers. The target web agent runs in one container, while AgentBreaker runs in another container and generates attack prompts that are evaluated against the target agent.

To reproduce the experimental setup described in the paper, follow the installation instructions below.

1. [Install Docker Engine on Ubuntu.](https://docs.docker.com/engine/install/ubuntu/#installation-methods)

2. [Install the NVIDIA Container Toolkit.](https://docs.nvidia.com/datacenter/cloud-native/container-toolkit/latest/install-guide.html)

3. Verify that the GPU is accessible inside the container.
   ```bash
   docker run --rm --gpus all testforsecpaper/yura:orig python3 -c "import torch; print(torch.cuda.get_device_name(0)); print('PASS')"
   ```
   > **Note:** Pulling the target container image may take up to 30 minutes depending on your network connection.

4. Build the **AgentBreaker image**
   ```bash
   docker build -t agentbreaker .
   ```

5. Copy `.env.example` to `.env` and update the required environment variables:

   > **Note:** The default values in `.env.example` can be used as-is. Simply set `GPT_API_KEY`.

   | Variable | Description | Values |
   |----------|-------------|--------|
   | `AGENT` | Target web agent | `YURA`, `SKYVERN`, `AGENTE` |
   | `ACTION` | Attacker's target action | `TERMINATE`, `CLICK`, `INPUT`, `PROMPT` |
   | `MODE` | Apply defense or not | `ATTACK`, `DEFENSE` |
   | `DEMO` | Evaluate only 5 of the 60 benchmark HTML pages  | `TRUE`, `FALSE` |
   | `BREAKER_LLM` | LLM used by AgentBreaker | `GPT`, `LLAMA` |
   | `GPT_API_KEY` | OpenAI API key | Provided in a HotCRP comment |
   | `LLAMA_API_KEY` | Llama API key | Provided in a HotCRP comment |

6. Start the **target agents container**

   ```bash
   ./run_target_agent.sh
   ```
   > **Note:** The target agent container will be running background.

   > [!important] 
   > Whenever the `.env` file is updated, rerun `./run_target_agent.sh` to restart the target agent before running a new experiment.

   

## Smoke Test

Verify that the target agent is running correctly and that AgentBreaker can successfully communicate with and monitor the target agent.

1. Run the smoke test.

   ```bash
   docker compose run --rm --service-ports agentbreaker python3 test_deploy_execute.py
   ```

2. If the output contains

   ```
   Status: Healthy
   ```

   then the artifact has been installed successfully.


<br>


# Step-by-Step Instructions

Skip to **Section D** if you only want to reproduce the experimental results.

## A. HTML Pages from Online-Mind2Web

The artifact includes 60 target HTML pages sampled from the [Online-Mind2Web](https://github.com/OSU-NLP-Group/Online-Mind2Web) benchmark.

This artifact supports the **Benchmark** paragraph in **Section 5.1 (Experimental Setup)** of the paper.

## B. AgentBreaker Source Code

```text
dataset/                 60 target HTML pages sampled from Online-Mind2Web.

framework/
├── composer.py          Implementation of the AgentBreaker Composer.
├── lmtester.py          Implementation of the AgentBreaker LM Tester.
├── evaluator.py         Implementation of the AgentBreaker Evaluator.
├── deployer/            Utilities for injecting attack payloads into target HTML pages.
└── prompt/              System and user prompts used by the AgentBreaker modules.

attack.py                Main pipeline for running AgentBreaker.
main.py                  Entry point for executing AgentBreaker.

agents/                  Target agent source code with evaluation-specific modifications and defense patches.

run_target_agent.sh      Script for launching the target agent.

test_deploy_execute.py   Smoke test for verifying both AgentBreaker and the target agent.
```

## C. Docker Images for Target Web Agents

Docker images for the evaluated web agents are provided separately via Docker Hub due to their large size:

- [`testforsecpaper/yura`](https://hub.docker.com/r/testforsecpaper/yura)
- [`testforsecpaper/agente`](https://hub.docker.com/r/testforsecpaper/agente)
- [`testforsecpaper/skyvern`](https://hub.docker.com/r/testforsecpaper/skyvern)

Each image is a Dockerized version of the corresponding open-source web agent:

- **YuraScanner**: https://github.com/pixelindigo/yurascanner/
- **Agent-E**: https://github.com/EmergenceAI/Agent-E
- **Skyvern**: https://github.com/skyvern-ai/skyvern

Only minimal modifications were made to the original source code to support the evaluation and implement the defense patches described in the paper. All modifications are located under `agents/{agent_name}/edit` and are marked with `# Edit`.

## D. Reproducing the Experimental Results

### 1. Attack Evaluation

> **Note:** This experiment supports the results reported in the **AgentBreaker** columns of **Table 1**. Due to API nondeterminism, exact numerical results may differ from those reported in the paper.

#### a. Configure the .env file as follows:

```dotenv
AGENT=SKYVERN
ACTION=INPUT
MODE=ATTACK
DEMO=TRUE

BREAKER_LLM=GPT
GPT_API_KEY=YOUR_API_KEY
LLAMA_API_KEY=YOUR_API_KEY

SECRET_FOR_LEAK_PROMPT=1q2w3e4r
```

#### b. Start the target agent
```bash
./run_target_agent.sh
```

#### c. Verify the setup
Run the smoke test and confirm that the output contains `Status: Healthy`.
```bash
docker compose run --rm --service-ports agentbreaker python3 test_deploy_execute.py
```

#### d. Run the experiment

```bash
docker compose run --rm --service-ports agentbreaker python3 main.py
```
**Estimated time:** A single run (`DEMO=TRUE`, 5 HTML pages) takes approximately **30 minutes**.
 
#### e. Check the results
After the experiment finishes, the terminal output reports the **Attack Success Rate (ASR)**, and other evaluation metrics. For reference, the corresponding results for this configuration are reported in the **INPUT** action for **Skyvern** in **Table 1** of the paper.

If you would like to reproduce the remaining results in **Table 1**, modify the corresponding variables in the `.env` file (e.g., `AGENT`, `ACTION`, `DEMO`, and `BREAKER_LLM`) and rerun the experiment. 


> [!IMPORTANT]
> After updating `.env` for another configuration, rerun `./run_target_agent.sh` to restart the target agent and verify it with a smoke test.


> **Note:** Docker images for **BrowserOS** and **NanoBrowser** are not included in this artifact. Due to implementation constraints, both agents require a headful browser environment and therefore cannot be reliably packaged as Docker images for our evaluation setup.

### 2. Defense Evaluation

> **Note:** This experiment supports the **Non-Adaptive** setting (**Both** row) reported in **Table 3**. Exact numerical results may vary depending on the execution environment and LLM outputs.

Set `MODE=DEFENSE` in the `.env` file, then follow the same procedure as in **Attack Evaluation**.


## E. Additional Results and Logs

By following the steps in **D. Reproducing the Experimental Results**, you can reproduce the results reported in **Table 1** and **Table 3** of the paper.

Optionally, if you would like to inspect the **internal behavior of AgentBreaker and the target agents** in more detail, refer to the logs below.

### 1. AgentBreaker Logs

The following directory contains the logs generated by each AgentBreaker module during optimization:

```text
_Agentbreaker_logs/SKYVERN_INPUT_ATTACK/{html_idx}/
```

| File | Description |
|------|-------------|
| `{epoch_idx}_a_strategy.log` | Accumulated CWI strategies |
| `{epoch_idx}_composer_prompt.log` | Prompt given to the Composer (system prompt + CWI strategies) |
| `{epoch_idx}_composer_response.log` | Composer output (generated adversarial phrase) |
| `{epoch_idx}_lmtester_lmtest_prompt.log` | Prompt given to the LM Tester (system prompt + adversarial phrase) |
| `{epoch_idx}_lmtester_lmtest_response.log` | LM Tester output (top-5 action rankings and the reasoning for the top-ranked action) |
| `{epoch_idx}_new_strategy_prompt.log` | Prompt given to the Strategist (system prompt + HTML page + LM Tester feedback) |
| `{epoch_idx}_new_strategy_response.log` | Strategist output (new CWI strategy) |

The final evaluation metrics for each HTML page are summarized in:

```text
_Agentbreaker_logs/SKYVERN_INPUT_ATTACK/{html_idx}/result_summary.log
```

| Field | Description |
|------|-------------|
| `html_index` | Index of the target HTML page |
| `epoch_used` | Number of optimization epochs |
| `success` | Whether the attack succeeded |
| `ui_text` | Generated adversarial phrase |
| `ui_text_length` | Length of the generated adversarial phrase |
| `optimization_time_sec` | Attack generation time (seconds) |

> **Note:** These logs are generated after running the experiments described in **D. Reproducing the Experimental Results**.

---

### 2. Target Agent Logs

Each target agent generates execution logs in its own vendor-specific format.
```text
_agent_logs/
```

To make these logs easier to understand, we additionally provide formatted sample logs in:

```text
_agent_logs/sample_agent_logs_{agent}_{action}_ATTACK/
```

The following descriptions highlight the key steps that demonstrate how each agent processes an injected webpage.

#### [Agent-E](_agent_logs/sample_agent_logs_AGENTE_CLICK_ATTACK/logs.md)

- `planner_agent` creates an initial plan for the user task.
- `browser_nav_executor` navigates to the target HTML page.
- `planner_agent` requests an inspection of the page.
- `browser_navigation_agent` reads the injected adversarial phrase while analyzing the DOM.
- `planner_agent` decides to click the `AdAdAd` button.
- `browser_nav_executor` executes the click action.

#### [Skyvern](_agent_logs/sample_agent_logs_SKYVERN_INPUT_ATTACK/logs/Step2_action_response.json)

- `Step0_completion_response.json` determines whether the user task has already been completed.
- `Step1_thought_response.json` reads the injected adversarial phrase and interprets entering `ISSTA` as a prerequisite for completing the task.
- `Step2_action_response.json` generates an `INPUT_TEXT` action to enter `ISSTA`.

#### [YuraScanner](_agent_logs/sample_agent_logs_YURA_TERMINATE_ATTACK/logs.md)

- The final action is generated from a single prompt without multi-turn planning.
- The injected adversarial phrase appears in the `CURRENT BROWSER CONTENT` section.
- Based on the injected phrase, the agent selects `STOP` as the final action in `YOUR COMMAND`.
  
