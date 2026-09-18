#!/usr/bin/env python3
"""Generate realistic K8s logs for testing log-trimmer."""

import random
import uuid
from datetime import datetime, timedelta

random.seed(42)

def rand_ip():
    return f"{random.randint(10,192)}.{random.randint(0,255)}.{random.randint(0,255)}.{random.randint(1,254)}"

def rand_mac():
    return ":".join(f"{random.randint(0,255):02x}" for _ in range(6))

def rand_uuid():
    return str(uuid.uuid4())

def rand_ts():
    base = datetime(2026, 4, 24, 0, 0, 0)
    delta = timedelta(seconds=random.randint(0, 86400))
    return (base + delta).strftime("%Y-%m-%dT%H:%M:%S.%fZ")

def rand_pod_name(ns="default"):
    prefixes = ["nginx", "redis", "postgres", "api-server", "worker", "cronjob", "ingress", "coredns", "prometheus", "grafana"]
    prefix = random.choice(prefixes)
    suffix = "".join(random.choices("abcdef0123456789", k=10))
    return f"{ns}/{prefix}-{suffix}"

def rand_container_name():
    return random.choice(["main", "sidecar", "init", "proxy", "logger"])

def rand_node():
    return f"node-{random.randint(1,20):03d}.cluster.internal"

lines = []

# --- 1. kubectl get pods -A style ---
for _ in range(500):
    pod = rand_pod_name(random.choice(["default", "kube-system", "monitoring", "app"]))
    status = random.choice(["Running", "Running", "Running", "Pending", "CrashLoopBackOff", "Completed", "Error"])
    restarts = random.randint(0, 50) if status != "Running" else random.randint(0, 3)
    age = f"{random.randint(1,365)}d{random.randint(0,23)}h" if status == "Running" else f"{random.randint(1,120)}m"
    lines.append(f"[{rand_ts()}] {pod}  1/1     {status}   {restarts}     {age}")

# --- 2. kubectl describe pod style ---
for _ in range(300):
    pod = rand_pod_name()
    node = rand_node()
    ip = rand_ip()
    ns = pod.split("/")[0]
    lines.append(f"[{rand_ts()}] Name:         {pod}")
    lines.append(f"[{rand_ts()}] Namespace:    {ns}")
    lines.append(f"[{rand_ts()}] Node:         {node}/{ip}")
    lines.append(f"[{rand_ts()}] Start Time:   {rand_ts()}")
    tpl_hash = random.randint(100000,999999)
    app = random.choice(["web","db","cache"])
    lines.append(f"[{rand_ts()}] Labels:       app={app}  pod-template-hash={tpl_hash}")
    lines.append(f"[{rand_ts()}] IP:           {ip}")
    lines.append(f"[{rand_ts()}] IPs:          IP: {ip}")
    lines.append(f"[{rand_ts()}] MAC:          {rand_mac()}")
    lines.append(f"[{rand_ts()}] Container ID: containerd://{rand_uuid()}")
    lines.append(f"[{rand_ts()}] State:        {random.choice(['Running','Waiting','Terminated'])}")
    if random.random() > 0.5:
        lines.append(f"[{rand_ts()}]  Started:      {rand_ts()}")
    ready = "True" if random.random() > 0.2 else "False"
    lines.append(f"[{rand_ts()}] Ready:          {ready}")
    lines.append(f"[{rand_ts()}] Restart Count:  {random.randint(0, 100)}")
    cpu = random.choice(["100m","250m","500m","1","2"])
    mem = random.choice(["128Mi","256Mi","512Mi","1Gi","2Gi"])
    lines.append(f"[{rand_ts()}] Limits:  cpu={cpu}  memory={mem}")
    cpu_r = random.choice(["50m","100m","250m"])
    mem_r = random.choice(["64Mi","128Mi","256Mi"])
    lines.append(f"[{rand_ts()}] Requests: cpu={cpu_r}  memory={mem_r}")
    lines.append(f"[{rand_ts()}] Environment:  <none>")
    mount_suffix = random.choice("abcdef0123456789")[:10]
    lines.append(f"[{rand_ts()}] Mounts:  /var/run/secrets/kubernetes.io/serviceaccount from kube-api-access-{mount_suffix} (ro)")

# --- 3. kubectl logs (container application logs) ---
log_levels = ["INFO", "WARN", "ERROR", "DEBUG", "FATAL"]
for _ in range(1000):
    ts = rand_ts()
    level = random.choice(log_levels)
    pod = rand_pod_name()
    container = rand_container_name()
    msg = random.choice([
        f"Request processed in {random.randint(1,5000)}ms",
        f"Connection to {rand_ip()}:{random.choice([80,443,8080,5432,6379])} established",
        f"Failed to connect to {rand_ip()}:{random.choice([80,443,8080,5432,6379])} - timeout after {random.randint(1,30)}s",
        f"Received signal {random.choice(['SIGTERM','SIGINT','SIGHUP'])}",
        f"Health check passed (latency={random.randint(1,100)}ms)",
        f"Health check failed: connection refused to {rand_ip()}",
        f"Database query took {random.randint(1,10000)}ms on {rand_ip()}:5432",
        f"Cache miss for key={rand_uuid()}",
        f"Cache hit for key={rand_uuid()}",
        f"Memory usage: {random.randint(50,95)}% ({random.randint(100,4000)}MB / {random.randint(2000,8000)}MB)",
        f"GC pause: {random.randint(1,500)}ms",
        f"Thread pool exhausted: active={random.randint(10,100)} max={random.choice([50,100,200])}",
        f"Retrying request to {rand_ip()} (attempt {random.randint(1,5)}/3)",
        f"TLS handshake failed with {rand_ip()}: certificate expired",
        f"DNS resolution failed for {random.choice(['api','db','cache','redis','postgres'])}.service.cluster.local",
        f"Pod {pod} started on node {rand_node()}",
        f"Pod {pod} terminated: exit code {random.choice([0,1,137,143,255])}",
        f"Container {container} pulling image {random.choice(['nginx','redis','postgres','python'])}:{random.choice(['latest','1.21','14-alpine','3.11'])}",
        f"Container {container} created with ID {rand_uuid()}",
        f"Container {container} started successfully",
        f"OOMKilled: container {container} exceeded memory limit {random.choice(['128Mi','256Mi','512Mi','1Gi'])}",
        f"Liveness probe failed: HTTP probe failed with statuscode: {random.choice([500,502,503,504])}",
        f"Readiness probe failed: connection refused to {rand_ip()}:{random.choice([8080,8443,9090])}",
        f'Pulling image "docker.io/library/{random.choice(["nginx","redis","postgres"])}:{random.choice(["latest","1.21"])}"',
        f'Successfully pulled image "{random.choice(["nginx","redis","postgres"])}:{random.choice(["latest","1.21"])}"',
    ])
    lines.append(f"[{ts}] [{level}] [{pod}/{container}] {msg}")

# --- 4. kubelet logs ---
for _ in range(500):
    ts = rand_ts()
    node = rand_node()
    pod = rand_pod_name()
    container = rand_container_name()
    ip = rand_ip()
    log_level = random.choice(["I", "W", "E"])
    seq = random.randint(100, 999)
    pid = random.randint(1, 999)
    lineno = random.randint(100, 2000)
    msg = random.choice([
        f"Pod {pod} is not scheduled: waiting",
        f"SyncLoop (PLEG): event for pod {pod}",
        f'Failed to pull image "{random.choice(["nginx","redis","postgres"])}:{random.choice(["latest","1.21"])}": rpc error: code = Unknown desc = failed to pull and unpack image',
        f"Error syncing pod {pod}, skipping: failed to StartContainer: Error response from daemon: rpc error: code = Unknown",
        f"Attempting to kill pod {pod} (Container {container})",
        f"Container {container} in pod {pod} is Ready",
        f"Started container {container} in pod {pod} with ID {rand_uuid()}",
        f'Failed to list *v1.Node: Get "https://{ip}:6443/api/v1/nodes": dial tcp {ip}:6443: connect: connection refused',
        f"Node {node} status update: Ready=True",
        f"Volume {rand_uuid()} mounted for pod {pod}",
    ])
    lines.append(f"[{ts}] {log_level}{seq}0424 {pid} kubelet.go:{lineno}] {msg}")

# --- 5. etcd logs ---
for _ in range(300):
    ts = rand_ts()
    level = random.choice(["INFO", "WARN"])
    msg = random.choice([
        f"compact: compacted revision {random.randint(1000000,9999999)} takes {random.randint(1,5000)}ms",
        f"snapshot: saved snapshot log index {random.randint(100000,9999999)}",
        f"applied: applied index {random.randint(1000000,9999999)} {random.randint(1,1000)}ms",
        f"committed: committed index {random.randint(1000000,9999999)} {random.randint(1,100)}ms",
        f"slow request: took {random.randint(100,10000)}ms but wanted {random.randint(10,100)}ms",
        f"publish: local member {rand_uuid()} published",
        f"rejected: rejected Raft message from {rand_uuid()}",
        f"leader changed: {rand_uuid()} -> {rand_uuid()}",
        f"new leader: elected {rand_uuid()} term {random.randint(1,100)}",
        f"peer {rand_ip()}:{random.choice([2380,2379])} is healthy",
    ])
    lines.append(f"[{ts}] {level} {msg}")

# --- 6. API server audit logs ---
for _ in range(400):
    ts = rand_ts()
    user = random.choice([
        "system:serviceaccount:kube-system:controller-manager",
        "system:admin",
        f"system:node:{rand_node()}",
        "user@example.com",
    ])
    verb = random.choice(["get", "list", "watch", "create", "update", "patch", "delete"])
    resource = random.choice(["pods", "services", "configmaps", "secrets", "deployments", "nodes", "events", "pods/log", "pods/status"])
    ns = random.choice(["", "default", "kube-system", "monitoring", "app"])
    ip = rand_ip()
    code = random.choice([200, 201, 403, 404, 500])
    result = random.choice(["success", "forbidden", "not-found", "internal-error"])
    msg = random.choice([
        f"AUDIT: user={user} verb={verb} resource={resource} namespace={ns} src={ip} responseCode={code}",
        f"AUDIT: {verb} /api/v1/{ns}/{resource} from {ip} user={user} result={result}",
    ])
    lines.append(f"[{ts}] {msg}")

# --- 7. Linux system logs (journalctl) ---
for _ in range(500):
    ts = rand_ts()
    hostname = rand_node()
    pid = random.randint(1000, 9999)
    msg = random.choice([
        f"{hostname} kernel: [{random.randint(1000,99999)}.{random.randint(100,999)}] {random.choice(['EXT4-fs','JBD2','device','CPU','memory'])} {random.choice(['sda','sdb','nvme0n1'])}: {random.choice(['mounted','detected','error','warning','info'])} {random.choice(['ext4','xfs'])}",
        f"{hostname} systemd[1]: {random.choice(['Started','Stopped','Starting','Stopping'])} {random.choice(['kubelet.service','docker.service','containerd.service','firewalld.service','sshd.service'])}.",
        f"{hostname} kubelet[{pid}]: {random.choice(['E0424','I0424','W0424'])} {random.randint(1,999)} kubelet.go:{random.randint(100,2000)} {random.choice(['Pod','Container','Volume','Node'])} {random.choice(['ready','failed','updated','created','deleted'])}",
        f'{hostname} docker[{pid}]: time="{rand_ts()}" level={random.choice(["info","warn","error"])} msg="{random.choice(["Container started","Container stopped","Image pulled","Network created","Volume mounted"])}" container={rand_uuid()}',
        f'{hostname} containerd[{pid}]: time="{rand_ts()}" level={random.choice(["info","warn","error"])} msg="{random.choice(["Starting containerd","Loading plugin","Serving GRPC API"])}" address={rand_ip()}:{random.choice([2376,2377,1024,1025])}',
        f"{hostname} sshd[{pid}]: {random.choice(['Accepted','Failed','Connection closed','Disconnected'])} {random.choice(['password','publickey','keyboard-interactive'])} for {random.choice(['root','admin','ubuntu','ec2-user'])} from {rand_ip()} port {random.randint(1024,65535)} ssh2",
        f"{hostname} CRON[{pid}]: ({random.choice(['root','admin'])}) CMD ({random.choice(['/usr/bin/','/opt/scripts/'])}{random.choice(['cleanup.sh','backup.sh','monitor.sh'])})",
        f"{hostname} systemd-logind[{pid}]: {random.choice(['New session','Removed session','Power key pressed'])} {random.randint(1,100)} of user {random.choice(['root','admin','ubuntu'])}",
        f"{hostname} NetworkManager[{pid}]: {random.choice(['<info','<warn','<error'])} {random.choice(['device changed state','connection activated','device disconnected','DHCP lease acquired'])} ({random.choice(['eth0','eth1','ens5','ens192'])}: {random.choice(['activated','deactivated','disconnected','connected'])})",
        f"{hostname} rsyslogd[{pid}]: {random.choice(['action resumed','action suspended','omfwd: TCP connect failed','main queue full'])} (module={random.choice(['omfwd','omfile','imuxsock'])})",
    ])
    lines.append(f"[{ts}] {msg}")

# Shuffle to simulate real interleaved logs
random.shuffle(lines)

with open("test_data/k8s_realistic.log", "w") as f:
    for line in lines:
        f.write(line + "\n")

print(f"Generated {len(lines)} log lines")
