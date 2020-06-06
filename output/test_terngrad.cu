#include <iostream>
#include <stdio.h>
#include <cuda.h>
#include <curand.h>
#include "cuda_runtime.h"

#include <thrust/execution_policy.h>
#include <thrust/reduce.h>
#include <thrust/functional.h>
#include <thrust/extrema.h>
#include <thrust/device_vector.h>
#include <thrust/host_vector.h>

#include "time_cost.hpp"
#include "TernGradEncode_body.h"
#include "get_policy_general.h"
#include "math.h"

struct smaller{
    __host__ __device__
    float operator()(const float& x, const float& y){
        if (x<y){
            return x;
        }
        return y;
    }
};
struct greater{
    __host__ __device__
    float operator()(const float& x, const float& y){
        if (x>y){
            return x;
        }
        return y;
    }
};

// const int N = 1 << 27;
#define N (1<<27)

int main(int argc, char** argv){
    zq_cpp_lib::time_cost zt;
    zt.start();
    // int N = atoi(argv[1]);
    // N = 1 << N;
    int repeat_times = atoi(argv[2]);
    int M = 10 + (N + 3 ) / 4;
    printf("N=%d\n", N);
    printf("M=%d\n", M);
    printf("repeat_times=%d\n", repeat_times);

    // float *devData;
    uint8_t* COMPRESSED;
    cudaStream_t stream;
    curandGenerator_t gen;
    cudaStreamCreate(&stream);
    zt.record("create stream");
    float* hostData;
    hostData = new float[N];
    // hostData = (float *)malloc(N*sizeof(float));
    zt.record("calloc");
    auto policy = zq_cpp_lib::operate_memory::get_policy<thrust::cuda_cub::par_t::stream_attachment_type>::get(stream);
    zt.record("get policy");
    float* devData;
    cudaMalloc((void **)&devData, N * sizeof(float));
    // thrust::device_vector<float> devData(N);
    cudaMalloc((void **)&COMPRESSED, M * sizeof(uint8_t));
    zt.record("cudaMalloc");
    curandCreateGenerator(&gen, CURAND_RNG_PSEUDO_DEFAULT);
    curandSetPseudoRandomGeneratorSeed(gen, 1234ULL);
    zt.record("curand initialize");
    curandGenerateUniform(gen, devData, N);
    curandGenerateUniform(gen, devData, N);
    zt.record("generate random twice");
    cudaMemcpy(hostData, devData, N * sizeof(float), cudaMemcpyDeviceToHost);
    zt.record("cudaMemcpy");
    cudaStreamSynchronize(stream);

    // float min_value = thrust::reduce(policy, devData, devData+N, 999, thrust::minimum<float>());
    // float max_value = thrust::reduce(policy, devData, devData+N, -99, greater());
    // float max_value = thrust::reduce(thrust::host, hostData, hostData+N, -99, greater());
    // float max_value = thrust::reduce(hostData, hostData+N, -99, greater());

    float data[6] = {1, 0, 2, 2, 1, 3};
    //hostData = {0.8872, 0.5674, 0.4511, 0.4172, 0.0838, 0.7606, ...}
    // hostData = data;

    auto ret_of_max_element = thrust::max_element(thrust::host, hostData, hostData+6);
    printf("ret_of_max_element=%f\n",*ret_of_max_element); //0.8872

    float max_value = thrust::reduce(thrust::host, hostData, hostData+6, -1, thrust::maximum<float>());
    // float max_value = thrust::reduce(thrust::host, hostData, hostData+N, -1, thrust::maximum<float>());
    printf("max_value=%f\n",max_value); //0.00

    float result = thrust::reduce(thrust::host, data, data + 6, -1,thrust::maximum<float>());
    printf("result=%f\n",result); // 3.00

    zt.record("call thrust::reduce");



    for (auto i = 0; i < 16; i++)
    {
        printf("%1.4f ", hostData[i]);
    }
    printf("\n");
    zt.record("print data");
    int ret;
    for (int j = 0; j < repeat_times; j++){
        TernGradEncode_body(
            devData,
            N,
            COMPRESSED,
            M,
            2,
            policy,
            stream
        );
        cudaMemcpy(hostData, devData, N * sizeof(float), cudaMemcpyDeviceToHost);

        for (auto i = 0; i < 16; i++)
        {
            printf("%1.4f ", hostData[i]);
        }
        printf("\n");
        printf("j=%d\tret=%d\n", j, ret);
    }
    zt.record("call TernGradEncode_body()");
    curandDestroyGenerator(gen);
    cudaFree(devData);
    cudaFree(COMPRESSED);
    zt.record("destroy");
    zt.print_by_us();

    printf("ret=%d\n",ret);

    return 0;
}