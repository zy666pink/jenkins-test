pipeline {
    agent any
    environment {
        harbor_ip = '10.0.0.225:8080'
        harbor_file = 'images'
        image_name = 'nginx'
        image_tag = "v${BUILD_NUMBER}" // 不推荐在此处使用
        images_name= "${image_name}:${image_tag}"
        push_pull_harbor = "${harbor_ip}/${harbor_file}/${images_name}"
        
        //部署变量
        container_name= "nginxlxlx"
        docker_port= "8085:80"
    }
     // 2. 优化：全局超时设置，防止任务卡死
    options {
        timeout(time: 5, unit: 'MINUTES') // 整个流水线超过10分钟自动终止
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
                        sh 'ls -l' // 列出文件确认
                    } catch (Exception e) {
                        echo "❌ 拉取代码失败: ${e.getMessage()}"
                        error("拉取代码失败: ${e.getMessage()}")
                    }
                }
            }
        }
        
               
              stage("构建镜像") {
                  steps {
                     sh "docker build -t ${images_name} ."
                  }
              }
       
       
       
             stage("推送镜像到harbor") {
                 steps {
                 withCredentials([usernamePassword(
                     credentialsId: "harbor-cicd-token",
                     passwordVariable: 'harbor_pd',
                     usernameVariable: 'harbor_user'
                     )]) {
                          sh "docker tag ${images_name} ${push_pull_harbor}"
                          sh "docker login ${harbor_ip} -u ${harbor_user} -p ${harbor_pd}"
                          sh "docker push ${push_pull_harbor}"
                          sh "docker logout ${harbor_ip}"
                          echo "✅ 镜像推送成功"

                     }
                 }
              }
       
             stage("拉取镜像并且在本地部署") {
                 steps {
                  sh "docker run -d -p ${docker_port} --name ${container_name} ${push_pull_harbor}"
                 }
             }
             
       
       
       
    }
    
    
    post {
        
        failure {
            echo "❌ 流水线执行失败，请检查日志"
        }
        
        success {
            echo "✅ 流水线执行成功，Nginx容器已部署完成"
            echo "🌐 访问地址: http://10.0.0.225:8085"
        }
    }
}

