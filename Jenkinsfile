pipeline {
    agent any
    environment {
        // 你的 Harbor 配置
        HARBOR_REGISTRY = '10.0.0.225'
        HARBOR_PROJECT = 'docker-images'
        IMAGE_NAME = 'my-app'
        IMAGE_TAG = "${BUILD_NUMBER}"
        FULL_IMAGE_NAME = "${HARBOR_REGISTRY}/${HARBOR_PROJECT}/${IMAGE_NAME}:${IMAGE_TAG}"
    }
    stages {
        stage('拉取代码') {
            steps {
                git url: 'https://github.com/zy666pink/jenkins-test.git',
                    credentialsId: 'jenkins-github-harbor-tuishonjinxian'
            }
        }

        stage('构建 Docker 镜像') {
            steps {
                // 关键修正：单引号改双引号，否则变量不解析
                sh "docker build -t ${FULL_IMAGE_NAME} ."
            }
        }

        stage('登录 Harbor 并推送镜像') {
            steps {
                script {
                    withCredentials([
                        usernamePassword(
                            credentialsId: 'harbor-cicd-token',
                            usernameVariable: 'HARBOR_USER',
                            passwordVariable: 'HARBOR_PWD'
                        )
                    ]) {
                        sh "docker login ${HARBOR_REGISTRY} -u ${HARBOR_USER} -p ${HARBOR_PWD}"
                        sh "docker push ${FULL_IMAGE_NAME}"
                    }
                }
            }
        }
    }
    post {
        success {
            echo "镜像推送成功: ${FULL_IMAGE_NAME}"
            // 可选：推送完成后清理本地镜像，节省磁盘
            sh "docker rmi ${FULL_IMAGE_NAME} || true"
        }
        failure {
            echo "构建或推送失败，请检查日志"
        }
    }
}
