pipeline {
    agent any
    // 引用参数化构建的变量（关键！）
    environment {
        HARBOR_IP       = '10.0.0.225:8080'
        HARBOR_PROJECT  = 'images'
        IMAGE_NAME      = 'nginx'
        // 替换1：用参数化的镜像标签，默认是v${BUILD_NUMBER}
        IMAGE_TAG       = "${params.IMAGE_TAG}"
        LOCAL_IMAGE     = "${IMAGE_NAME}:${IMAGE_TAG}"
        HARBOR_IMAGE    = "${HARBOR_IP}/${HARBOR_PROJECT}/${LOCAL_IMAGE}"
        // 替换2：用参数化的容器名
        CONTAINER_NAME  = "${params.CONTAINER_NAME}"
        // 替换3：用参数化的部署端口
        DEPLOY_PORT     = "${params.DEPLOY_PORT}"
    }
    options {
        timeout(time: 10, unit: 'MINUTES')
    }

    stages {
        stage('清理工作目录') { steps { cleanWs() } }
        
        stage('拉取代码') {
            steps {
                script {
                    try {
                        // 替换4：用参数化的分支拉代码
                        git url: 'https://github.com/zy666pink/jenkins-test.git',
                            credentialsId: 'github-token',
                            branch: "${params.BRANCH_NAME}" // 引用分支参数
                        echo "✅ 拉取${params.BRANCH_NAME}分支代码成功"
                    } catch (Exception e) {
                        echo "❌ 拉取代码失败: ${e.getMessage()}"
                        error("中止流水线：拉取代码失败")
                    }
                }
            }
        }
        
        // 质量门禁、构建镜像、推送Harbor步骤不变（变量已自动引用参数）
        
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
                    // 替换5：用参数化的部署端口启动容器
                    sh "docker run -d -p ${DEPLOY_PORT} --name ${CONTAINER_NAME} ${HARBOR_IMAGE}"
                    sh "sleep 3"
                    sh "docker ps --filter name=${CONTAINER_NAME}"
                    echo "✅ 容器部署成功，访问地址: http://<你的Jenkins服务器IP>:${DEPLOY_PORT%:*}"
                }
            }
            post {
                failure {
                    echo "🧹 部署失败，清理残留容器..."
                    sh "docker stop ${CONTAINER_NAME} || true"
                    sh "docker rm ${CONTAINER_NAME} || true"
                }
            }
        }
    }
    // post兜底逻辑不变
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
            echo "🌐 访问地址: http://<你的Jenkins服务器IP>:${DEPLOY_PORT%:*}"
        }
    }
}
