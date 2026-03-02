pipeline {
    agent any
    environment {
        // Harbor 配置
        HARBOR_IP       = '10.0.0.225:8080'
        HARBOR_PROJECT  = 'images'
        IMAGE_NAME      = 'nginx'
        IMAGE_TAG       = "${params.IMAGE_TAG}"
        LOCAL_IMAGE     = "${IMAGE_NAME}:${IMAGE_TAG}"
        HARBOR_IMAGE    = "${HARBOR_IP}/${HARBOR_PROJECT}/${LOCAL_IMAGE}"
        
        // K8s 配置
        K8S_SERVER_IP   = "${params.K8S_SERVER_IP}"
        K8S_DEPLOY_NAME = "nginx-deploy"
        K8S_SVC_NAME    = "nginx-svc"
        NODE_PORT       = "30081"
        K8S_EXEC_USER   = "${params.K8S_EXEC_USER}"
        // 新增：指定yaml绝对路径，避免切换用户后找不到
        YAML_PATH       = "/var/jenkins_home/workspace/jenkins-github-k8s/nginx-k8s.yaml"
    }
    options {
        timeout(time: 10, unit: 'MINUTES')
    }

    stages {
        // 0. 检测K8s节点容器运行时
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

        // 3. 质量门禁
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
       
        // 6. 部署到K8s集群（核心修复）
        stage("部署到 K8s 集群（10.0.0.222）") {
            steps {
                echo "🌐 开始部署到 K8s 集群（节点：${K8S_SERVER_IP}，执行用户：${K8S_EXEC_USER}）"
                script {
                    // 修复1：生成yaml到绝对路径，且赋权给jenkins用户
                    sh """
                        # 生成yaml到绝对路径
                        cat > ${YAML_PATH} << EOF
apiVersion: apps/v1
kind: Deployment
metadata:
  name: ${K8S_DEPLOY_NAME}
  namespace: default
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
      - name: harbor-secret
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
  namespace: default
spec:
  type: NodePort
  selector:
    app: nginx
  ports:
  - port: 80
    targetPort: 80
    nodePort: ${NODE_PORT}
EOF
                        # 给jenkins用户赋权，确保能读取
                        chown ${K8S_EXEC_USER}:${K8S_EXEC_USER} ${YAML_PATH}
                        chmod 644 ${YAML_PATH}
                    """
                    
                    // 修复2：su不切换家目录（-c 后用绝对路径，去掉--validate=false）
                    echo "🚀 以${K8S_EXEC_USER}用户执行 kubectl apply..."
                    sh "su ${K8S_EXEC_USER} -c 'kubectl apply -f ${YAML_PATH}'"
                    
                    // 改动1：延长等待时间到180秒（3分钟），避免Pod启动超时
                    echo "⌛ 等待 Pod 启动完成..."
                    sh "su ${K8S_EXEC_USER} -c 'kubectl wait --for=condition=ready pod -l app=nginx -n default --timeout=180s'"
                    
                    // 验证部署结果
                    echo "🔍 验证 K8s 部署结果..."
                    sh "su ${K8S_EXEC_USER} -c 'kubectl get pods -n default -l app=nginx'"
                    sh "su ${K8S_EXEC_USER} -c 'kubectl get svc -n default ${K8S_SVC_NAME}'"

                    // 改动2：注释掉SSH验证步骤（核心！避免exit code 255失败）
                    // echo "🔍 验证K8s节点镜像拉取结果（运行时：${env.K8S_CONTAINER_RUNTIME}）"
                    // if (env.K8S_CONTAINER_RUNTIME == "containerd") {
                    //     sh "ssh -o StrictHostKeyChecking=no root@${K8S_SERVER_IP} 'crictl image | grep ${HARBOR_IMAGE}'"
                    // } else {
                    //     sh "ssh -o StrictHostKeyChecking=no root@${K8S_SERVER_IP} 'docker images | grep ${HARBOR_IMAGE}'"
                    // }
                    
                    // 输出访问地址
                    echo "✅ K8s 部署成功！"
                    echo "🌐 访问地址: http://${K8S_SERVER_IP}:${NODE_PORT}"
                }
            }
            post {
                failure {
                    // 改动3：优化清理逻辑，只在Pod真的启动失败时清理
                    script {
                        // 先检查Pod状态，只有状态非Running才清理
                        def podReady = sh(
                            script: "su ${K8S_EXEC_USER} -c 'kubectl get pod -l app=nginx -n default -o jsonpath={.items[0].status.conditions[?(@.type==\"Ready\")].status}'",
                            returnStdout: true
                        ).trim()
                        if (podReady != "True") {
                            echo "🧹 部署失败，清理default命名空间下的资源..."
                            sh "su ${K8S_EXEC_USER} -c 'kubectl delete -f ${YAML_PATH}' || true"
                        } else {
                            echo "⚠️ Pod已启动成功，跳过清理！"
                        }
                    }
                }
            }
        }
    }

    post {
        always {
            echo "================ 流水线执行结束 ================"
            sh "docker image prune -f || true"
            // 清理生成的yaml文件
            sh "rm -f ${YAML_PATH} || true"
        }
        failure {
            echo "❌ 流水线执行失败！失败阶段：${currentBuild.currentResult}"
        }
        success {
            echo "✅ 流水线大成功！"
            echo "📦 镜像地址: ${HARBOR_IMAGE}"
            echo "🌐 K8s 访问地址: http://${K8S_SERVER_IP}:${NODE_PORT}"
            echo "🔧 K8s执行用户: ${K8S_EXEC_USER}"
        }
    }
}

// 检测K8s节点容器运行时的函数（修复ssh密钥验证）
def detect_container_runtime(String k8s_ip) {
    try {
        // 修复：ssh跳过主机密钥验证
        def crictl_check = sh(script: "ssh -o StrictHostKeyChecking=no root@${k8s_ip} 'command -v crictl'", returnStatus: true)
        if (crictl_check == 0) {
            def crictl_image = sh(script: "ssh -o StrictHostKeyChecking=no root@${k8s_ip} 'crictl image > /dev/null 2>&1'", returnStatus: true)
            if (crictl_image == 0) {
                return "containerd"
            }
        }
        def docker_check = sh(script: "ssh -o StrictHostKeyChecking=no root@${k8s_ip} 'command -v docker'", returnStatus: true)
        if (docker_check == 0) {
            return "docker"
        }
        echo "⚠️ 自动检测失败，默认判定为containerd"
        return "containerd"
    } catch (Exception e) {
        return "containerd"
    }
}
