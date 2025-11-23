"""
Docker container lifecycle management for integration tests.
Handles starting, stopping, and health checking of test containers.
"""

import subprocess
import time
import os
import sys
from typing import List, Optional
import logging

logger = logging.getLogger(__name__)


class DockerManager:
    """Manages Docker containers for integration testing."""
    
    def __init__(self, compose_file: str = "docker-compose.test.yml", project_name: str = "teapot-integration-tests"):
        """
        Initialize the Docker manager.
        
        Args:
            compose_file: Path to the docker-compose file
            project_name: Docker Compose project name
        """
        self.compose_file = os.path.abspath(compose_file)
        self.project_name = project_name
        self.project_root = os.path.dirname(self.compose_file)
        
        if not os.path.exists(self.compose_file):
            raise FileNotFoundError(f"Docker Compose file not found: {self.compose_file}")
    
    def _run_command(self, command: List[str], check: bool = True, capture_output: bool = True) -> subprocess.CompletedProcess:
        """
        Run a shell command.
        
        Args:
            command: Command and arguments as a list
            check: Whether to raise an exception on non-zero exit
            capture_output: Whether to capture stdout/stderr
            
        Returns:
            CompletedProcess instance
        """
        logger.debug(f"Running command: {' '.join(command)}")
        return subprocess.run(
            command,
            cwd=self.project_root,
            check=check,
            capture_output=capture_output,
            text=True
        )
    
    def is_docker_available(self) -> bool:
        """Check if Docker is installed and running."""
        try:
            result = self._run_command(["docker", "info"], check=False)
            return result.returncode == 0
        except FileNotFoundError:
            return False
    
    def is_compose_available(self) -> bool:
        """Check if Docker Compose is available."""
        try:
            result = self._run_command(["docker", "compose", "version"], check=False)
            return result.returncode == 0
        except FileNotFoundError:
            return False
    
    def start_containers(self, services: Optional[List[str]] = None, timeout: int = 120) -> bool:
        """
        Start Docker containers.
        
        Args:
            services: List of specific services to start (None for all)
            timeout: Maximum time to wait for containers to be healthy (seconds)
            
        Returns:
            True if containers started successfully, False otherwise
        """
        if not self.is_docker_available():
            logger.error("Docker is not available. Please ensure Docker is installed and running.")
            return False
        
        if not self.is_compose_available():
            logger.error("Docker Compose is not available.")
            return False
        
        logger.info(f"Starting Docker containers from {self.compose_file}...")
        
        cmd = [
            "docker", "compose",
            "-f", self.compose_file,
            "-p", self.project_name,
            "up", "-d", "--build", "--remove-orphans"
        ]
        
        if services:
            cmd.extend(services)
        
        try:
            result = self._run_command(cmd, capture_output=False)
            
            if result.returncode == 0:
                logger.info("Containers started. Waiting for health checks...")
                return self.wait_for_healthy(timeout=timeout)
            else:
                logger.error("Failed to start containers")
                return False
                
        except subprocess.CalledProcessError as e:
            logger.error(f"Error starting containers: {e}")
            return False
    
    def stop_containers(self, remove_volumes: bool = False) -> bool:
        """
        Stop Docker containers.
        
        Args:
            remove_volumes: Whether to remove volumes
            
        Returns:
            True if containers stopped successfully, False otherwise
        """
        logger.info("Stopping Docker containers...")
        
        cmd = [
            "docker", "compose",
            "-f", self.compose_file,
            "-p", self.project_name,
            "down"
        ]
        
        if remove_volumes:
            cmd.append("-v")
        
        try:
            result = self._run_command(cmd, capture_output=False)
            
            if result.returncode == 0:
                logger.info("Containers stopped successfully")
                return True
            else:
                logger.error("Failed to stop containers")
                return False
                
        except subprocess.CalledProcessError as e:
            logger.error(f"Error stopping containers: {e}")
            return False
    
    def get_container_status(self) -> dict:
        """
        Get the status of all containers.
        
        Returns:
            Dictionary with container statuses
        """
        cmd = [
            "docker", "compose",
            "-f", self.compose_file,
            "-p", self.project_name,
            "ps", "--format", "json"
        ]
        
        try:
            result = self._run_command(cmd)
            if result.returncode == 0 and result.stdout:
                import json
                # Handle both single JSON object and multiple JSON objects
                output = result.stdout.strip()
                if output.startswith('['):
                    return {"containers": json.loads(output)}
                else:
                    # Multiple JSON objects, one per line
                    containers = [json.loads(line) for line in output.split('\n') if line.strip()]
                    return {"containers": containers}
            return {"containers": []}
        except Exception as e:
            logger.warning(f"Could not get container status: {e}")
            return {"containers": []}
    
    def wait_for_healthy(self, timeout: int = 120, poll_interval: int = 2) -> bool:
        """
        Wait for all containers to be healthy.
        
        Args:
            timeout: Maximum time to wait (seconds)
            poll_interval: Time between checks (seconds)
            
        Returns:
            True if all containers are healthy, False if timeout
        """
        import requests
        start_time = time.time()
        
        # Give containers initial time to start
        logger.info("Waiting for containers to initialize...")
        time.sleep(5)
        
        while time.time() - start_time < timeout:
            status = self.get_container_status()
            containers = status.get("containers", [])
            
            if not containers:
                logger.warning("No containers found")
                time.sleep(poll_interval)
                continue
            
            all_healthy = True
            unhealthy_services = []
            
            for container in containers:
                service_name = container.get("Service", container.get("name", "unknown"))
                health = container.get("Health", "")
                state = container.get("State", "")
                
                # Consider container healthy if it's running
                if state != "running":
                    all_healthy = False
                    unhealthy_services.append(f"{service_name} (state: {state})")
                elif health and health != "healthy" and health != "":
                    all_healthy = False
                    unhealthy_services.append(f"{service_name} (health: {health})")
            
            # Additional check: try to connect to user-service
            if all_healthy:
                try:
                    # Simple TCP connection check
                    import socket
                    sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
                    sock.settimeout(2)
                    result = sock.connect_ex(('localhost', 8081))
                    sock.close()
                    
                    if result == 0:
                        logger.info("All containers are healthy and services are accessible!")
                        return True
                    else:
                        unhealthy_services.append("user-service (port not accessible)")
                        all_healthy = False
                except Exception as e:
                    logger.debug(f"Service check failed: {e}")
                    unhealthy_services.append(f"user-service (connection failed)")
                    all_healthy = False
            
            elapsed = int(time.time() - start_time)
            logger.info(f"Waiting for containers to be ready... ({elapsed}s/{timeout}s)")
            if unhealthy_services:
                logger.debug(f"Not ready: {', '.join(unhealthy_services)}")
            
            time.sleep(poll_interval)
        
        logger.error(f"Timeout waiting for containers to be healthy after {timeout}s")
        self.show_logs()
        return False
    
    def show_logs(self, tail: int = 50) -> None:
        """
        Show logs from containers.
        
        Args:
            tail: Number of lines to show from the end of logs
        """
        cmd = [
            "docker", "compose",
            "-f", self.compose_file,
            "-p", self.project_name,
            "logs", "--tail", str(tail)
        ]
        
        try:
            self._run_command(cmd, capture_output=False, check=False)
        except Exception as e:
            logger.error(f"Error showing logs: {e}")
    
    def restart_service(self, service: str) -> bool:
        """
        Restart a specific service.
        
        Args:
            service: Name of the service to restart
            
        Returns:
            True if restart successful, False otherwise
        """
        logger.info(f"Restarting service: {service}")
        
        cmd = [
            "docker", "compose",
            "-f", self.compose_file,
            "-p", self.project_name,
            "restart", service
        ]
        
        try:
            result = self._run_command(cmd, capture_output=False)
            return result.returncode == 0
        except subprocess.CalledProcessError as e:
            logger.error(f"Error restarting service {service}: {e}")
            return False
    
    def cleanup(self, remove_volumes: bool = True) -> None:
        """
        Full cleanup: stop containers and optionally remove volumes.
        
        Args:
            remove_volumes: Whether to remove volumes
        """
        logger.info("Performing cleanup...")
        self.stop_containers(remove_volumes=remove_volumes)


def main():
    """CLI interface for manual container management."""
    import argparse
    
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s [%(levelname)s] %(message)s'
    )
    
    parser = argparse.ArgumentParser(description="Manage Docker containers for integration tests")
    parser.add_argument(
        "action",
        choices=["up", "down", "restart", "status", "logs"],
        help="Action to perform"
    )
    parser.add_argument(
        "--service",
        help="Specific service name (for restart action)"
    )
    parser.add_argument(
        "--remove-volumes",
        action="store_true",
        help="Remove volumes when stopping (for down action)"
    )
    parser.add_argument(
        "--compose-file",
        default="docker-compose.test.yml",
        help="Path to docker-compose file"
    )
    
    args = parser.parse_args()
    
    manager = DockerManager(compose_file=args.compose_file)
    
    if args.action == "up":
        success = manager.start_containers()
        sys.exit(0 if success else 1)
    
    elif args.action == "down":
        success = manager.stop_containers(remove_volumes=args.remove_volumes)
        sys.exit(0 if success else 1)
    
    elif args.action == "restart":
        if not args.service:
            logger.error("--service is required for restart action")
            sys.exit(1)
        success = manager.restart_service(args.service)
        sys.exit(0 if success else 1)
    
    elif args.action == "status":
        status = manager.get_container_status()
        import json
        print(json.dumps(status, indent=2))
    
    elif args.action == "logs":
        manager.show_logs()


if __name__ == "__main__":
    main()
