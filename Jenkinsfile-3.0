pipeline {
    agent any
    environment {
        HARBOR_IP       = '10.0.0.225:8080'
        HARBOR_PROJECT  = 'images'
        IMAGE_NAME      = 'nginx'
        IMAGE_TAG       = "${params.IMAGE_TAG}"       // 镜像标签参数
        LOCAL_IMAGE     = "${IMAGE_NAME}:${IMAGE_TAG}"
        HARBOR_IMAGE    = "${HARBOR_IP}/${HARBOR_PROJECT}/${LOCAL_IMAGE}"
        CONTAINER_NAME  = "${params.CONTAINER_NAME}"   // 容器名参数
        DEPLOY_PORT     = "${params.DEPLOY_PORT}"      // 部署端口参数
        JENKINS_IP      = "${params.JENKINS_SERVER_IP}"// Jenkins服务器IP参数
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
                        git url: 'https://github.com/zy666pink/jenkins-test.git',
                            credentialsId: 'github-token',
                            branch: "${params.BRANCH_NAME}" // 分支参数
                        echo "✅ 拉取${params.BRANCH_NAME}分支代码成功"
                    } catch (Exception e) {
                        echo "❌ 拉取代码失败: ${e.getMessage()}"
                        error("中止流水线：拉取代码失败")
                    }
                }
            }
        }

        // 质量门禁步骤（补全，避免流程缺失）
        stage('代码/文件检查（质量门禁）') {
            steps {
                echo "🔍 开始检查关键文件..."
                script {
                    def dockerfileExists = fileExists 'Dockerfile'
                    if (!dockerfileExists) {
                        error("❌ 关键文件缺失：仓库里没有Dockerfile，无法构建镜像！")
                    }
                    echo "✅ Dockerfile 存在"

                    def indexExists = fileExists 'index.html'
                    if (!indexExists) {

                        error("❌ 关键文件缺失：仓库里没有index.html，镜像内容为空！")
                    }
                    echo "✅ index.html 存在"
                }
            }
        }
        
        // 构建镜像步骤（补全）
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
       
        // 推送Harbor步骤（补全）
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
                    sh "docker run -d -p ${DEPLOY_PORT} --name ${CONTAINER_NAME} ${HARBOR_IMAGE}"
                    sh "sleep 3"
                    sh "docker ps --filter name=${CONTAINER_NAME}"
                    // 替换为参数化IP，修复语法报错
                    echo "✅ 容器部署成功，访问地址: http://${JENKINS_IP}:${DEPLOY_PORT}"
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
            // 替换为参数化IP
            echo "🌐 访问地址: http://${JENKINS_IP}:${DEPLOY_PORT}"
        }
    }
}
