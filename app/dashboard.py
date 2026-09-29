import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
import os
import sys

# Ensure imports work from parent dir
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))
from src.data_loader import DataLoader
from src.simulator import Simulator
from src.decision_engine import DecisionEngine
from src.sensitivity import SensitivityAnalyzer

st.set_page_config(page_title="Rightsizing Simulator", layout="wide")

st.title("Performance-Safe Rightsizing Simulator")
st.markdown("Evaluate whether an environment can be safely migrated to a cheaper instance type without violating performance/availability SLOs.")

# --- Data Loading ---
@st.cache_data
def load_data():
    loader = DataLoader('data')
    return loader.load_environments(), loader.load_telemetry(), loader.load_pricing()

envs_df, telemetry_df, pricing_df = load_data()

INSTANCE_CATALOG = {
    'small': {'vcpu': 2, 'memory_gb': 8, 'base_price': 0.05},
    'medium': {'vcpu': 4, 'memory_gb': 16, 'base_price': 0.10},
    'large': {'vcpu': 8, 'memory_gb': 32, 'base_price': 0.20}
}
sim = Simulator(INSTANCE_CATALOG, pricing_df)

# --- Sidebar Configuration ---
st.sidebar.header("1. Select Environment")
env_id = st.sidebar.selectbox("Environment ID", envs_df['environment_id'].tolist())

env_info = envs_df[envs_df['environment_id'] == env_id].iloc[0]
current_inst = env_info['current_instance_type']

st.sidebar.markdown(f"**Service:** {env_info['service_name']}")
st.sidebar.markdown(f"**Current Instance:** {current_inst} ({INSTANCE_CATALOG[current_inst]['vcpu']} vCPU, {INSTANCE_CATALOG[current_inst]['memory_gb']} GB)")

st.sidebar.header("2. Simulation Settings")
candidate_inst = st.sidebar.selectbox("Candidate Instance", list(INSTANCE_CATALOG.keys()), index=0)
latency_target = st.sidebar.slider("P95 Latency Target (ms)", 100, 500, 250, 10)
availability_target = st.sidebar.slider("Availability Target (%)", 90.0, 99.99, 99.9, 0.01)
traffic_growth = st.sidebar.slider("Traffic Growth Assumption (%)", -20, 100, 0, 5) / 100.0

# --- Filtering Telemetry ---
env_telemetry = telemetry_df[telemetry_df['environment_id'] == env_id]

# --- Baseline Metrics (Overview) ---
st.header("Historical Baseline")
col1, col2, col3, col4 = st.columns(4)

baseline = sim.run_simulation(env_telemetry, current_inst, current_inst)['baseline']
if baseline:
    col1.metric("Peak CPU", f"{baseline['peak_cpu']:.1f}%")
    col2.metric("Peak Memory", f"{baseline['peak_memory']:.1f}%")
    col3.metric("P95 Latency", f"{baseline['p95_latency']:.1f} ms")
    col4.metric("Avg Availability", f"{baseline['measured_availability']:.2f}%")

st.markdown("### Historical Trends")
tcol1, tcol2 = st.columns(2)
with tcol1:
    fig_cpu = px.line(env_telemetry, x='timestamp', y='cpu_utilization_pct', title='CPU Utilization (%)')
    st.plotly_chart(fig_cpu, use_container_width=True)
with tcol2:
    fig_req = px.line(env_telemetry, x='timestamp', y='request_volume', title='Request Volume')
    st.plotly_chart(fig_req, use_container_width=True)

# --- Tabs ---
tab1, tab2 = st.tabs(["Traditional Workflow", "🤖 Agentic Rightsizing"])

with tab1:
    # --- Simulation Execution ---
    st.header("Simulation Results")
    sim_res = sim.run_simulation(env_telemetry, current_inst, candidate_inst, latency_target, availability_target, traffic_growth)
    
    if st.button("Run Simulation", type="primary", key="btn_sim_trad"):
        decision, reasons = DecisionEngine.evaluate(sim_res)
        
        # Decision Banner
        if decision == "SAFE TO RIGHTSIZE":
            st.success(f"### 🟢 {decision}")
        elif decision == "INSUFFICIENT DATA":
            st.warning(f"### 🟡 {decision}")
        else:
            st.error(f"### 🔴 {decision}")
            
        for r in reasons:
            st.markdown(f"- {r}")
            
        st.markdown("---")
        
        rcol1, rcol2, rcol3 = st.columns(3)
        cost = sim_res['cost_eval']
        slo = sim_res['slo_eval']
        
        with rcol1:
            st.markdown("#### Cost Comparison")
            st.metric("Baseline Monthly", f"${cost['baseline_monthly_cost']:.2f}")
            st.metric("Simulated Monthly", f"${cost['simulated_monthly_cost']:.2f}", delta=f"-{cost['cost_reduction_pct']:.1f}%", delta_color="normal")
            
        with rcol2:
            st.markdown("#### Performance (P95 Latency)")
            st.metric("Baseline", f"{baseline['p95_latency']:.1f} ms")
            delta_lat = slo['projected_p95_latency'] - baseline['p95_latency']
            st.metric("Simulated", f"{slo['projected_p95_latency']:.1f} ms", delta=f"{delta_lat:.1f} ms", delta_color="inverse")
            
        with rcol3:
            st.markdown("#### Reliability (Availability)")
            st.metric("Baseline", f"{baseline['measured_availability']:.2f}%")
            delta_avail = slo['projected_availability'] - baseline['measured_availability']
            st.metric("Simulated", f"{slo['projected_availability']:.2f}%", delta=f"{delta_avail:.2f}%", delta_color="normal")
    
        st.markdown("### Projected Workload Distribution")
        pdf = sim_res['projected_performance']
        fig_proj = go.Figure()
        fig_proj.add_trace(go.Box(y=env_telemetry['cpu_utilization_pct'], name="Baseline CPU"))
        fig_proj.add_trace(go.Box(y=pdf['projected_cpu'], name="Projected CPU"))
        st.plotly_chart(fig_proj, use_container_width=True)
        
        from src.analysis import AnalysisEngine, StakeholderViews
        st.header("Candidate Comparison (Cost/Performance Tradeoff)")
        tradeoff = AnalysisEngine.cost_performance_tradeoff(baseline, sim_res) # baseline is a dict here but we need sim_res style for current
        sim_curr = sim.run_simulation(env_telemetry, current_inst, current_inst, latency_target, availability_target, traffic_growth)
        tradeoff = AnalysisEngine.cost_performance_tradeoff(sim_curr, sim_res)
        if tradeoff:
            st.json(tradeoff)
            
        st.header("Stakeholder Views")
        st.markdown("**INFRASTRUCTURE ENGINEER**")
        infra_view = StakeholderViews.get_infrastructure_engineer_view(env_id, {"cpu_projection": sim_res['peak_cpu'], "decision": decision}, "HEALTHY" if decision == "SAFE TO RIGHTSIZE" else "N/A")
        st.json(infra_view)
        
        st.markdown("**SERVICE OWNER**")
        so_view = StakeholderViews.get_service_owner_view({"latency_projection": slo['projected_p95_latency'], "availability_projection": slo['projected_availability'], "decision": decision})
        st.json(so_view)
        
        explanation = AnalysisEngine.generate_explanation(decision, current_inst, candidate_inst, sim_res, reasons)
        with st.expander("Explainability: WHY this decision?"):
            st.json(explanation)
    
        # --- Migration Lifecycle (LOCAL MOCK INFRASTRUCTURE) ---
        st.header("Migration Lifecycle (LOCAL MOCK INFRASTRUCTURE)")
        st.markdown("This section demonstrates an executable localhost migration lifecycle using a local mock infrastructure state.")
        
        from src.orchestrator import MigrationOrchestrator
        from src.mock_infrastructure import LocalInfrastructure
        from src.audit_log import AuditLog
        
        # Initialize mock infrastructure in session state
        if 'infrastructure' not in st.session_state:
            st.session_state.infrastructure = LocalInfrastructure()
            for e in envs_df['environment_id']:
                st.session_state.infrastructure.register_environment(e, envs_df[envs_df['environment_id'] == e].iloc[0]['current_instance_type'])
                
        if 'audit_log' not in st.session_state:
            st.session_state.audit_log = AuditLog("data/dashboard_audit_log.csv")
            
        orchestrator = MigrationOrchestrator(sim, st.session_state.infrastructure, st.session_state.audit_log)
        
        current_mock_state = st.session_state.infrastructure.get_instance_state(env_id)
        events = st.session_state.audit_log.get_events_for_env(env_id)
        last_event = events[-1]['event'] if events else None
    
        st.markdown("### Migration Control")
        st.markdown(f"**Current Instance**: `{current_inst}`")
        st.markdown(f"**Candidate Instance**: `{candidate_inst}`")
        st.markdown(f"**Mock Infrastructure State**: `{current_mock_state}`")
    
        if decision != "SAFE TO RIGHTSIZE":
            st.error("State: **BLOCKED**")
            st.markdown(f"Migration is disabled. Reason: {reasons[0]}")
        else:
            if current_mock_state == current_inst:
                if last_event == "ROLLBACK_COMPLETED":
                    st.info("State: **ROLLED BACK**")
                    st.success("Original instance restored.")
                else:
                    st.success("State: **READY / SAFE TO MIGRATE**")
                
                simulate_failure = st.checkbox("SIMULATED FAILURE INJECTION (Force post-migration failure)")
                if st.button("Execute Local Migration", type="primary", key="btn_mig_exec"):
                    approved, precheck_msg, updated_sim_res = orchestrator.pre_migration_check(
                        env_id, current_inst, candidate_inst, env_telemetry, 
                        target_latency=latency_target, target_availability=availability_target
                    )
                    if approved:
                        success, exec_msg = orchestrator.execute_migration(
                            env_id, current_inst, candidate_inst, 
                            monitoring_scenario="persistent_failure" if simulate_failure else "stable", 
                            sim_res=updated_sim_res
                        )
                        st.rerun()
                    else:
                        st.error(f"Pre-check failed: {precheck_msg}")
    
            elif current_mock_state == candidate_inst:
                st.info("State: **MIGRATED / ROLLBACK AVAILABLE**")
                if st.button("Rollback Migration", type="secondary", key="btn_mig_rb"):
                    orchestrator.trigger_rollback(env_id, current_inst, candidate_inst, "User triggered manual rollback")
                    st.rerun()
                    
        st.markdown("### Audit Log")
        if events:
            st.dataframe(pd.DataFrame(events))
        else:
            st.write("No events recorded for this environment yet.")
    
        # --- Sensitivity Analysis ---
        st.header("Sensitivity Analysis")
        st.markdown("How does the decision change with varying traffic growth?")
        sa = SensitivityAnalyzer(sim)
        sa_res = sa.analyze_traffic_growth(env_telemetry, current_inst, candidate_inst, latency_target, availability_target)
        sa_df = pd.DataFrame(sa_res)
        st.dataframe(sa_df[['traffic_growth_pct', 'decision', 'p95_latency', 'cost_saving']])

with tab2:
    st.header("🤖 Agentic Rightsizing Workflow")
    st.markdown("This tab demonstrates the fully autonomous agent loop: `OBSERVE -> ANALYZE -> PLAN -> VALIDATE -> EXECUTE -> VERIFY -> RE-PLAN`.")
    
    from src.agent import RightsizingAgent
    from src.agent_tools import AgentTools
    from src.mock_infrastructure import LocalInfrastructure
    from src.audit_log import AuditLog
    
    if 'infrastructure' not in st.session_state:
        st.session_state.infrastructure = LocalInfrastructure()
        for e in envs_df['environment_id']:
            st.session_state.infrastructure.register_environment(e, envs_df[envs_df['environment_id'] == e].iloc[0]['current_instance_type'])
    if 'audit_log' not in st.session_state:
        st.session_state.audit_log = AuditLog("data/dashboard_audit_log.csv")
    
    agent_mode = st.radio("Agent Mode", ["Single Environment", "Portfolio Analysis (All Environments)"])
    
    if agent_mode == "Single Environment":
        st.markdown(f"**Target Environment**: `{env_id}`")
        failure_mode = st.selectbox("Deterministic Failure Injection", ["NORMAL", "CPU_FAILURE", "MEMORY_FAILURE", "LATENCY_FAILURE", "AVAILABILITY_FAILURE"])
        
        if st.button("Run Agent Analysis", type="primary", key="btn_run_agent"):
            st.markdown("---")
            st.markdown("### Agent Execution Log")
            
            tools = AgentTools(sim, st.session_state.infrastructure, st.session_state.audit_log)
            agent = RightsizingAgent(tools)
            
            # The agent will autonomously pick the candidate based on simple logic if needed, 
            # but we can pass the UI selected candidate to observe its trace.
            trace = agent.run_lifecycle(env_id, candidate_inst, failure_mode)
            
            col_s1, col_s2, col_s3, col_s4 = st.columns(4)
            col_s1.metric("Agent Status", agent.state)
            col_s2.metric("Risk Level", agent.risk_level)
            col_s3.metric("Selected Candidate", candidate_inst)
            col_s4.metric("Failure Mode", failure_mode)
            
            if agent.state == "COMPLETED":
                st.success("Outcome: MIGRATION SUCCESSFUL")
            elif agent.state == "ROLLED_BACK":
                st.warning("Outcome: ROLLED BACK DUE TO HEALTH CHECK FAILURE")
            elif agent.state == "BLOCKED":
                st.error("Outcome: BLOCKED BY SAFETY ENGINE")
            else:
                st.error(f"Outcome: {agent.state}")
                
            st.markdown("### Agent Trace")
            for t in trace:
                with st.expander(f"[{t['step']}] {t['state']} - Tool: {t['action']}"):
                    st.write(f"**Result**: {t['result']}")
                    if 'details' in t:
                        st.json(t['details'])
                        
    else:
        st.markdown("**Target**: `All 73 Environments`")
        if st.button("Run Portfolio Analysis", type="primary", key="btn_run_portfolio"):
            tools = AgentTools(sim, st.session_state.infrastructure, st.session_state.audit_log)
            agent = RightsizingAgent(tools)
            safe_envs, blocked_envs = agent.analyze_portfolio(envs_df['environment_id'].tolist())
            
            st.success(f"Portfolio Analysis Complete! Found {len(safe_envs)} Safe Opportunities and {len(blocked_envs)} Blocked Environments.")
            
            st.markdown("### Safe Recommendations (Ranked by Savings)")
            st.dataframe(pd.DataFrame(safe_envs))
            
            st.markdown("### Blocked Migrations")
            st.dataframe(pd.DataFrame(blocked_envs))
            
            from src.analysis import AnalysisEngine, StakeholderViews
            portfolio_res = AnalysisEngine.portfolio_optimization(envs_df, telemetry_df, orchestrator)
            st.markdown("### FinOps View")
            finops_view = StakeholderViews.get_finops_view(portfolio_res['summary'])
            st.json(finops_view)
