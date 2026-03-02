pipeline {
    agent any
    environment {
        HARBOR_IP       = '10.0.0.225:8080'
        HARBOR_PROJECT  = 'images'
        IMAGE_NAME      = 'nginx'
        IMAGE_TAG       = "v${BUILD_NUMBER}"
        LOCAL_IMAGE     = "${IMAGE_NAME}:${IMAGE_TAG}"
        HARBOR_IMAGE    = "${HARBOR_IP}/${HARBOR_PROJECT}/${LOCAL_IMAGE}"
        CONTAINER_NAME  = "nginxlxlx"
        HOST_PORT       = "8085"
        CONTAINER_PORT  = "80"
    }
    options {
        timeout(time: 10, unit: 'MINUTES') // 超时兜底
    }

    stages {
        stage('清理工作目录') {
            steps {
                cleanWs()
            }
        }
        
        stage('拉取代码') {
            steps {
                script {
                    try {
                        git url: 'https://github.com/zy666pink/jenkins-test.git',
                            credentialsId: 'github-token',
                            branch: 'master'
                        echo "✅ 拉取代码成功"
                    } catch (Exception e) {
                        echo "❌ 拉取代码失败: ${e.getMessage()}"
                        error("中止流水线：拉取代码失败")
                    }
                }
            }
        }

        // ========== 新增：质量门禁（核心） ==========
        stage('代码/文件检查（质量门禁）') {
            steps {
                echo "🔍 开始检查关键文件..."
                script {
                    // 检查Dockerfile是否存在
                    def dockerfileExists = fileExists 'Dockerfile'
                    if (!dockerfileExists) {
                        error("❌ 关键文件缺失：仓库里没有Dockerfile，无法构建镜像！")
                    }
                    echo "✅ Dockerfile 存在"

                    // 检查index.html是否存在（自定义检查）
                    def indexExists = fileExists 'index.html'
                    if (!indexExists) {
                        error("❌ 关键文件缺失：仓库里没有index.html，镜像内容为空！")
                    }
                    echo "✅ index.html 存在"

                    // 可选：检查脚本是否可执行（比如test_hello.sh）
                    if (fileExists 'test_hello.sh') {
                        sh "chmod +x test_hello.sh" // 加执行权限
                        echo "✅ 测试脚本已赋权"
                    }
                }
            }
        }
        // ==========================================
        
        stage("构建镜像") {
            steps {
                echo "🚀 开始构建镜像: ${LOCAL_IMAGE}"
                sh "docker build -t ${LOCAL_IMAGE} ."
                sh "docker images | grep ${IMAGE_NAME}"
            }
            // ========== 新增：构建失败清理 ==========
            post {
                failure {
                    echo "🧹 构建失败，清理临时镜像..."
                    sh "docker rmi ${LOCAL_IMAGE} || true"
                }
            }
        }
       
        stage("推送镜像到 Harbor") {
            steps {
                echo "📤 开始推送镜像到 Harbor"
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
       
        stage("拉取镜像并在本地部署") {
            steps {
                echo "🌐 开始部署容器: ${CONTAINER_NAME}"
                script {
                    sh """
                        if [ \$(docker ps -a -q -f name=${CONTAINER_NAME}) ]; then
                            docker stop ${CONTAINER_NAME} || true
                            docker rm ${CONTAINER_NAME} || true
                            echo "旧容器已清理"
                        fi
                    """
                    sh "docker pull ${HARBOR_IMAGE}"
                    sh "docker run -d -p ${HOST_PORT}:${CONTAINER_PORT} --name ${CONTAINER_NAME} ${HARBOR_IMAGE}"
                    sh "sleep 3"
                    sh "docker ps --filter name=${CONTAINER_NAME}"
                    echo "✅ 容器部署成功，访问地址: http://<你的Jenkins服务器IP>:${HOST_PORT}"
                }
            }
            // ========== 新增：部署失败清理 ==========
            post {
                failure {
                    echo "🧹 部署失败，清理残留容器..."
                    sh "docker stop ${CONTAINER_NAME} || true"
                    sh "docker rm ${CONTAINER_NAME} || true"
                }
            }
        }
    }
    
    // ========== 新增：全局兜底（无论成功/失败都执行） ==========
    post {
        always {
            echo "================ 流水线执行结束 ================"
            sh "docker image prune -f || true" // 清理悬空镜像
        }
        failure {
            echo "❌ 流水线执行失败！失败阶段：${currentBuild.currentResult}"
            echo "🔍 失败原因：${currentBuild.description}"
        }
        success {
            echo "✅ 流水线大成功！"
            echo "📦 镜像地址: ${HARBOR_IMAGE}"
            echo "🌐 访问地址: http://<你的Jenkins服务器IP>:${HOST_PORT}"
        }
    }
}
