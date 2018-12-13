/* VNF emulation using memory accesses
author:
Raphael Durner,
Chair of Communication Networks,
Technical University of Munich
*/
#include <iostream>
#include <string>
#include <random>   /* srand, rand */
#include <time.h>       /* time */
#include <map>
#include <math.h> 
#include <chrono>



using namespace std;

int checkParams(int argc,char *argv[])
{
	if(argc!=4)
	{
	cout<<"Usage: "<<argv[0]<<" <K packets per second> <allocated memory in KBytes> <alpha>"<<"\n";
	return -1;
	}
	int pps(stoi(argv[1]));
	int memSize(stoi(argv[2]));
	float alpha(stof(argv[3]));
	if(!(pps>0) | !(memSize>0) | !(alpha>=0))
	{
	cout<<"Usage: "<<argv[0]<<" <K packets per second> <allocated memory in KBytes> <alpha>"<<"\n";
	cout<<"Arguments have to be larger than 0 (or in case of alpha larger or equal)!"<<"\n";
	return -1;
	}
	return 0;
}


int main(int argc, char *argv[])
{    
	if(checkParams(argc,argv)!=0)
	return -1;
	uint_fast32_t memSize=stoi(argv[2])*250;
	long tpp=(double)1e6/stoi(argv[1]);//time per packet in ns
	double alpha=std::stof(argv[3]);

	const uint_fast32_t reps=(1e7/tpp)+int((memSize/1e5));
		
	uint32_t * table;
	uint_fast32_t mem_pos;

	clock_t now_c,start_c,need_c;//clocks for wait computation	
	struct timespec sleep_t = {0};//used for nanosleep
	sleep_t.tv_sec = 0;
	sleep_t.tv_nsec=max(tpp,1L);
	uint_fast32_t t_busy; //busytime in us
	uint_fast32_t t_all=0,t_cycle=0; //time in ns
	uint_fast32_t proc_pack=0; //number of processed packets

	/* initialize random generator: */
	random_device rd;  //Will be used to obtain a seed for the random number engine
	default_random_engine gen(rd()); //Standard mersenne_twister_engine seeded with rd()
	uniform_real_distribution<> dis(0.0, 1.0);
	/*init table*/
	table = (uint32_t*) malloc (memSize*sizeof(uint32_t));
	for(int i=0;i<memSize;i++)
	{
		table[i]=0;
	}
	cout<<"timestamp,rate\n";
	auto start= chrono::system_clock::now();
	start_c=clock();
	while(true)
	{
		
		for(int j=0;j<=reps;j++)
		{
	    mem_pos=memSize*(1-pow((1-dis(gen)),1/(alpha+1)));
			table[mem_pos]++;    
		}
		now_c=clock();
		need_c=now_c-start_c;
		start_c=now_c;
		t_busy=((double)need_c)/CLOCKS_PER_SEC*1e9;
		sleep_t.tv_nsec=max(0L,long(tpp*reps-t_busy));
		nanosleep(&sleep_t,(struct timespec *)NULL);
		t_cycle+=t_busy+sleep_t.tv_nsec;
		proc_pack+=reps;
		if(t_cycle>=1e9)
		{
			auto now = chrono::system_clock::now();
			auto diff = std::chrono::duration_cast< chrono::duration<int,std::milli> >( now.time_since_epoch() );
			cout<< diff.count()<<","<<proc_pack/(t_cycle/(uint_fast32_t ) 1e9)<<"\n";
			cout.flush();
			proc_pack=0;
			t_cycle=0;
		}
	}
	return 0;
}



