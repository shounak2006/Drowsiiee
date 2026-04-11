import React, { useRef } from 'react';
import { Canvas, useFrame } from '@react-three/fiber';
import { Torus, MeshDistortMaterial, Environment } from '@react-three/drei';

function GlowingCore({ status }) {
  const meshRef = useRef();

  useFrame((state, delta) => {
    if (meshRef.current) {
      meshRef.current.rotation.x += delta * 0.5;
      meshRef.current.rotation.y += delta * 0.8;
      
      if (status === 'CRITICAL') {
        const scale = 1 + Math.sin(state.clock.elapsedTime * 10) * 0.1;
        meshRef.current.scale.set(scale, scale, scale);
      } else {
        meshRef.current.scale.lerp({ x: 1, y: 1, z: 1 }, 0.1);
      }
    }
  });

  const getColor = () => {
    switch (status) {
      case 'SAFE': return '#00fca8';
      case 'WARNING': return '#fbbf24';
      case 'CRITICAL': return '#ff3366';
      default: return '#00e5ff';
    }
  };

  return (
    <group>
      <Torus ref={meshRef} args={[1.5, 0.4, 32, 100]}>
        <MeshDistortMaterial 
          color={getColor()}
          emissive={getColor()}
          emissiveIntensity={status === 'CRITICAL' ? 2 : 1.2}
          distort={status === 'CRITICAL' ? 0.6 : 0.3}
          speed={status === 'CRITICAL' ? 5 : 2}
          roughness={0.2}
        />
      </Torus>
    </group>
  );
}

export function ThreeVisualizer({ status }) {
  return (
    <div className="w-full h-full min-h-[300px] flex items-center justify-center relative">
      <Canvas camera={{ position: [0, 0, 5] }}>
        <ambientLight intensity={0.5} />
        <pointLight position={[10, 10, 10]} intensity={1} />
        <GlowingCore status={status} />
        <Environment preset="city" />
      </Canvas>
    </div>
  );
}
