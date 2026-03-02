pipeline {
    agent any
    environment {
        // Harbor 配置（225服务器的Harbor）
        HARBOR_IP       = '10.0.0.225:8080'
        HARBOR_PROJECT  = 'images'
        IMAGE_NAME      = 'nginx'
        IMAGE_TAG       = "${params.IMAGE_TAG}"
        LOCAL_IMAGE     = "${IMAGE_NAME}:${IMAGE_TAG}"
        HARBOR_IMAGE    = "${HARBOR_IP}/${HARBOR_PROJECT}/${LOCAL_IMAGE}"
        
        // K8s 配置（固定default命名空间）
        K8S_SERVER_IP   = "${params.K8S_SERVER_IP}" // K8s节点IP：10.0.0.222
        K8S_DEPLOY_NAME = "nginx-deploy"
        K8S_SVC_NAME    = "nginx-svc"
        NODE_PORT       = "30080" // K8s的NodePort端口
    }
    options {
        timeout(time: 10, unit: 'MINUTES') // 超时时间10分钟
    }

    stages {
        // 0. 检测K8s节点的容器运行时（Docker/Containerd）
        stage('检测K8s节点容器运行时') {
            steps {
                script {
                    def runtime = detect_container_runtime(K8S_SERVER_IP)
                    env.K8S_CONTAINER_RUNTIME = runtime
                    echo "✅ K8s节点(${K8S_SERVER_IP})的容器运行时：${runtime}"
                }
            }
        }

        // 1. 清理工作目录
        stage('清理工作目录') { 
            steps { cleanWs() } 
        }
        
        // 2. 拉取GitHub代码
        stage('拉取代码') {
            steps {
                script {
                    try {
                        git url: 'https://github.com/zy666pink/jenkins-test.git',
                            credentialsId: 'github-token',
                            branch: "${params.BRANCH_NAME}"
                        echo "✅ 拉取${params.BRANCH_NAME}分支代码成功"
                    } catch (Exception e) {
                        echo "❌ 拉取代码失败: ${e.getMessage()}"
                        error("中止流水线：拉取代码失败")
                    }
                }
            }
        }

        // 3. 质量门禁（检查关键文件）
        stage('代码/文件检查（质量门禁）') {
            steps {
                echo "🔍 开始检查关键文件..."
                script {
                    def dockerfileExists = fileExists 'Dockerfile'
                    if (!dockerfileExists) {
                        error("❌ 关键文件缺失：仓库里没有Dockerfile！")
                    }
                    echo "✅ Dockerfile 存在"

                    def indexExists = fileExists 'index.html'
                    if (!indexExists) {
                        error("❌ 关键文件缺失：仓库里没有index.html！")
                    }
                    echo "✅ index.html 存在"
                }
            }
        }
        
        // 4. 构建Docker镜像
        stage("构建镜像") {
            steps {
                echo "🚀 开始构建镜像: ${LOCAL_IMAGE}"
                sh "docker build -t ${LOCAL_IMAGE} ."
                sh "docker images | grep ${IMAGE_NAME}"
            }
            post {
                failure {
                    echo "🧹 构建失败，清理临时镜像..."
                    sh "docker rmi ${LOCAL_IMAGE} || true"
                }
            }
        }
       
        // 5. 推送镜像到Harbor仓库
        stage("推送镜像到 Harbor") {
            steps {
                echo "📤 开始推送镜像到 Harbor（10.0.0.225:8080）"
                withCredentials([usernamePassword(
                    credentialsId: "harbor-cicd-token",
                    passwordVariable: 'HARBOR_PD',
                    usernameVariable: 'HARBOR_USER'
                )]) {
                    sh "docker tag ${LOCAL_IMAGE} ${HARBOR_IMAGE}"
                    sh "echo ${HARBOR_PD} | docker login ${HARBOR_IP} -u ${HARBOR_USER} --password-stdin"
                    sh "docker push ${HARBOR_IMAGE}"
                    sh "docker logout ${HARBOR_IP}"
                    echo "✅ 镜像推送成功: ${HARBOR_IMAGE}"
                }
            }
            post {
                success {
                    echo "🧹 推送成功，清理本地镜像..."
                    sh "docker rmi ${LOCAL_IMAGE} ${HARBOR_IMAGE} || true"
                }
                failure {
                    echo "🧹 推送失败，清理临时镜像..."
                    sh "docker rmi ${LOCAL_IMAGE} ${HARBOR_IMAGE} || true"
                }
            }
        }
       
        // 6. 部署到K8s集群（全程default命名空间）
        stage("部署到 K8s 集群（10.0.0.222）") {
            steps {
                echo "🌐 开始部署到 K8s 集群（节点：${K8S_SERVER_IP}，namespace: default）"
                script {
                    // 动态生成K8s YAML（固定default命名空间）
                    sh """
                        cat > nginx-k8s.yaml << EOF
apiVersion: apps/v1
kind: Deployment
metadata:
  name: ${K8S_DEPLOY_NAME}
  namespace: default  # 固定default命名空间
spec:
  replicas: 1
  selector:
    matchLabels:
      app: nginx
  template:
    metadata:
      labels:
        app: nginx
    spec:
      imagePullSecrets:
      - name: harbor-secret # default命名空间下的密钥
      containers:
      - name: nginx
        image: ${HARBOR_IMAGE}
        ports:
        - containerPort: 80
        resources:
          limits:
            cpu: 100m
            memory: 128Mi
          requests:
            cpu: 50m
            memory: 64Mi
---
apiVersion: v1
kind: Service
metadata:
  name: ${K8S_SVC_NAME}
  namespace: default  # 固定default命名空间
spec:
  type: NodePort
  selector:
    app: nginx
  ports:
  - port: 80
    targetPort: 80
    nodePort: ${NODE_PORT}
EOF
                    """
                    
                    // 应用YAML到default命名空间
                    echo "🚀 执行 kubectl apply 部署应用..."
                    sh "kubectl apply -f nginx-k8s.yaml"
                    
                    // 等待Pod启动（default命名空间）
                    echo "⌛ 等待 Pod 启动完成..."
                    sh "kubectl wait --for=condition=ready pod -l app=nginx -n default --timeout=60s"
                    
                    // 验证部署结果（default命名空间）
                    echo "🔍 验证 K8s 部署结果（default命名空间）..."
                    sh "kubectl get pods -n default -l app=nginx"
                    sh "kubectl get svc -n default ${K8S_SVC_NAME}"

                    // 验证镜像拉取（Containerd/docker适配）
                    echo "🔍 验证K8s节点镜像拉取结果（运行时：${env.K8S_CONTAINER_RUNTIME}）"
                    if (env.K8S_CONTAINER_RUNTIME == "containerd") {
                        sh "ssh root@${K8S_SERVER_IP} 'crictl image | grep ${HARBOR_IMAGE}'"
                    } else {
                        sh "ssh root@${K8S_SERVER_IP} 'docker images | grep ${HARBOR_IMAGE}'"
                    }
                    
                    // 输出访问地址
                    echo "✅ K8s 部署成功！"
                    echo "🌐 访问地址: http://${K8S_SERVER_IP}:${NODE_PORT}"
                }
            }
            post {
                failure {
                    echo "🧹 部署失败，清理default命名空间下的资源..."
                    sh "kubectl delete -f nginx-k8s.yaml || true"
                }
            }
        }
    }

    // 流水线结束兜底逻辑
    post {
        always {
            echo "================ 流水线执行结束 ================"
            sh "docker image prune -f || true"
        }
        failure {
            echo "❌ 流水线执行失败！失败阶段：${currentBuild.currentResult}"
            echo "🔍 失败原因：${currentBuild.description}"
        }
        success {
            echo "✅ 流水线大成功！"
            echo "📦 镜像地址: ${HARBOR_IMAGE}"
            echo "🌐 K8s 访问地址: http://${K8S_SERVER_IP}:${NODE_PORT}"
            echo "🔧 K8s节点容器运行时: ${env.K8S_CONTAINER_RUNTIME}"
            echo "📌 所有资源部署在default命名空间"
        }
    }
}

// 自定义函数：检测K8s节点容器运行时（Docker/Containerd）
def detect_container_runtime(String k8s_ip) {
    try {
        // 优先检测containerd
        def crictl_check = sh(script: "ssh root@${k8s_ip} 'command -v crictl'", returnStatus: true)
        if (crictl_check == 0) {
            def crictl_image = sh(script: "ssh root@${k8s_ip} 'crictl image > /dev/null 2>&1'", returnStatus: true)
            if (crictl_image == 0) {
                return "containerd"
            }
        }
        // 检测docker
        def docker_check = sh(script: "ssh root@${k8s_ip} 'command -v docker'", returnStatus: true)
        if (docker_check == 0) {
            return "docker"
        }
        // 兜底判定为containerd（适配你的环境）
        echo "⚠️ 自动检测失败，默认判定为containerd"
        return "containerd"
    } catch (Exception e) {
        return "containerd"
    }
}
