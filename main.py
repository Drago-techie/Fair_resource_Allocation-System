import streamlit as st
import pandas as pd

class Process:
    def __init__(self, pid, burst_time, priority):
        self.pid = str(pid)
        self.burst_time = burst_time
        self.remaining_time = burst_time
        self.base_priority = priority
        self.current_priority = priority
        self.waiting_time = 0

class Scheduler:
    def __init__(self, aging_rate=1):
        self.ready_queue = []
        self.running_process = None
        self.aging_rate = aging_rate
        self.completed_processes = []
        self.time = 0

    def add_process(self, process):
        self.ready_queue.append(process)
        self.sort_queue()

    def sort_queue(self):
        self.ready_queue.sort(key=lambda x: x.current_priority, reverse=True)

    def tick(self):
        if self.running_process:
            self.running_process.remaining_time -= 1
            if self.running_process.remaining_time <= 0:
                self.completed_processes.append(self.running_process)
                self.running_process = None

        for p in self.ready_queue:
            p.waiting_time += 1
            p.current_priority = p.base_priority + (p.waiting_time * self.aging_rate)

        self.sort_queue()

        if not self.running_process and self.ready_queue:
            self.running_process = self.ready_queue.pop(0)
            self.running_process.waiting_time = 0
        elif self.running_process and self.ready_queue:
            if self.ready_queue[0].current_priority > self.running_process.current_priority:
                self.ready_queue.append(self.running_process)
                self.running_process = self.ready_queue.pop(0)
                self.running_process.waiting_time = 0
                self.sort_queue()

        self.time += 1

st.set_page_config(page_title="Fair Resource Allocation System", layout="wide")

st.markdown("""
    <style>
    div[data-baseweb="slider"] div[role="slider"] {
        background-color: #AECBFA !important;
        border: 2px solid #1e1e1e !important;
        border-radius: 10px !important;
        height: 24px !important;
        width: 10px !important;
    }
    div[data-baseweb="slider"] div[data-testid="stSliderTickBar"] > div {
        background-color: #AECBFA !important;
    }
    </style>
""", unsafe_allow_html=True)

if 'scheduler' not in st.session_state:
    st.session_state.scheduler = Scheduler(aging_rate=1)
    
    default_processes = [
        Process("1", 10, 20),
        Process("2", 2, 50),
        Process("3", 8, 5),
        Process("4", 4, 15)
    ]
    for p in default_processes:
        st.session_state.scheduler.add_process(p)

scheduler = st.session_state.scheduler

with st.sidebar:
    st.header("Add New Process")
    
    with st.form("add_process_form", border=True):
        new_pid = st.text_input("Process ID", value=f"P{len(scheduler.ready_queue) + len(scheduler.completed_processes) + 5}")
        new_burst = st.number_input("Burst Time", min_value=1, value=5)
        new_pri = st.number_input("Base Priority", min_value=0, value=10)
        
        submitted = st.form_submit_button("Add to Queue")
        if submitted:
            scheduler.add_process(Process(new_pid, int(new_burst), int(new_pri)))
            st.success(f"Added Process {new_pid}")
            st.rerun()

    st.header("Manual Priority Override")
    if scheduler.ready_queue:
        with st.form("override_form", border=True):
            target_pid = st.selectbox("Select Process", [p.pid for p in scheduler.ready_queue])
            new_manual_pri = st.slider("New Current Priority", min_value=0, max_value=100, value=50)
            override_submitted = st.form_submit_button("Update Priority")
            
            if override_submitted:
                for p in scheduler.ready_queue:
                    if p.pid == target_pid:
                        p.current_priority = new_manual_pri
                        p.base_priority = new_manual_pri
                        p.waiting_time = 0
                        break
                scheduler.sort_queue()
                st.success(f"Updated PID {target_pid}")
                st.rerun()
    else:
        st.info("No processes in queue.")

    st.divider()
    if st.button("Reset Simulation", type="secondary"):
        del st.session_state.scheduler
        st.rerun()

st.title("Fair Resource Allocation System")
st.markdown("Watch how long-waiting processes dynamically increase their priority to prevent starvation.")

col1, col2 = st.columns([1, 3])

with col1:
    st.button("Advance 1 Tick", on_click=scheduler.tick, type="primary", use_container_width=True)
    
    with st.container(border=True):
        st.metric("System Clock", f"{scheduler.time} Ticks")
        
        if scheduler.running_process:
            rp = scheduler.running_process
            st.info(f"**RUNNING:** PID {rp.pid}\n\nTime Left: {rp.remaining_time}\n\nPriority: {rp.current_priority}")
        else:
            st.warning("**RUNNING:** CPU IDLE")

with col2:
    with st.container(border=True):
        st.subheader("Ready Queue")
        if scheduler.ready_queue:
            queue_data = [{
                "PID": p.pid,
                "Remaining Time": p.remaining_time,
                "Base Priority": p.base_priority,
                "Current Priority": p.current_priority,
                "Wait Time": p.waiting_time
            } for p in scheduler.ready_queue]
            
            df_queue = pd.DataFrame(queue_data)
            st.dataframe(
                df_queue, 
                use_container_width=True,
                hide_index=True,
                column_config={
                    "Current Priority": st.column_config.ProgressColumn(
                        "Current Priority",
                        help="Increases as wait time grows",
                        format="%d",
                        min_value=0,
                        max_value=max([p.current_priority for p in scheduler.ready_queue] + [100])
                    )
                }
            )
        else:
            st.write("Queue is empty.")

if scheduler.completed_processes:
    st.divider()
    with st.container(border=True):
        st.subheader("Completed Processes")
        completed_data = [{"PID": p.pid, "Burst Time": p.burst_time, "Base Priority": p.base_priority} for p in scheduler.completed_processes]
        st.dataframe(pd.DataFrame(completed_data), use_container_width=True, hide_index=True)