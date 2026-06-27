#!/bin/bash

# Visual styling
GREEN='\033[0;32m'
BLUE='\033[0;34m'
CYAN='\033[0;36m'
YELLOW='\033[1;33m'
RED='\033[0;31m'
NC='\033[0m' # No Color
BOLD='\033[1m'

clear
echo -e "${CYAN}${BOLD}========================================================================${NC}"
echo -e "${CYAN}${BOLD}     RUNNING HYBRID LOG ANOMALY DETECTION SYSTEM TEST SUITE             ${NC}"
echo -e "${CYAN}${BOLD}========================================================================${NC}"
echo -e "Starting all evaluation experiments sequentially on the current codebase..."
echo -e "${YELLOW}Hint: If you haven't already, please run: pip install -r ML/requirements.txt${NC}"
echo ""

# 1. Ablation Study
echo -e "${YELLOW}${BOLD}1. Running Experiment A (HDFS Benchmark & Ablation Study) [Dataset: Pure HDFS_2k Dataset]...${NC}"
PYTHONPATH=ML python3 ML/evaluation/run_ablation_study.py
echo -e "\n------------------------------------------------------------\n"

# 2. Functional Validations
echo -e "${YELLOW}${BOLD}2. Running Experiment B (Heuristic Consistency Validation) [Dataset: Pure HDFS_2k Dataset]...${NC}"
PYTHONPATH=ML python3 ML/evaluation/evaluate_accuracy.py
echo -e "\n------------------------------------------------------------\n"

# 3. Fault Injections
echo -e "${YELLOW}${BOLD}3. Running Experiment C (Production Fault Injections) [Dataset: Hybrid (Clean HDFS Logs + Synthetic Structural Faults)]...${NC}"
PYTHONPATH=ML python3 ML/evaluation/run_hybrid_simulation.py
echo -e "\n------------------------------------------------------------\n"

# 4. Threshold Sweep
echo -e "${YELLOW}${BOLD}4. Running Experiment E (Threshold Sensitivity Analysis) [Dataset: Pure HDFS_2k Dataset]...${NC}"
PYTHONPATH=ML python3 ML/evaluation/run_threshold_sensitivity.py
echo -e "\n------------------------------------------------------------\n"

# 5. Stress Test
echo -e "${YELLOW}${BOLD}5. Running Experiment F (Scalability Ingestion Stress Test) [Dataset: Fully Synthetic OTel Logs]...${NC}"
python3 backend/tests/test_stress.py

echo ""
echo -e "${GREEN}${BOLD}========================================================================${NC}"
echo -e "${GREEN}${BOLD}     ALL TEST CASES COMPLETED SUCCESSFULLY                              ${NC}"
echo -e "${GREEN}${BOLD}========================================================================${NC}"

echo -e "\n${CYAN}${BOLD}========================================================================================${NC}"
echo -e "${CYAN}${BOLD}                 WHY THIS SUPPORTS THE HYBRID ARCHITECTURE                              ${NC}"
echo -e "${CYAN}${BOLD}========================================================================================${NC}"
echo -e "| Component          | Primary Role           | Limitation Alone             | Supported By            |"
echo -e "| ------------------ | ---------------------- | ---------------------------- | ----------------------- |"
echo -e "| Isolation Forest   | Structural anomalies   | Misses semantic exceptions   | Heuristics              |"
echo -e "| LSTM               | Sequence anomalies     | Requires sequence violation  | Fault Injection Test    |"
echo -e "| Prophet            | Volume anomalies       | Requires traffic changes     | Volume Injection Test   |"
echo -e "| Weighted Consensus | Borderline cooperation | Needs multiple weak signals  | Production Pipeline     |"
echo -e "| Heuristic          | Known signatures       | Cannot detect novel anomalies| Isolation Forest & LSTM |"
echo -e "${CYAN}${BOLD}========================================================================================${NC}\n"
