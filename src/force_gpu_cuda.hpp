#pragma once
#include <iostream>
#include <particle_simulator.hpp>
#include "soft_ptcl.hpp"

#ifdef GPU_PROFILE
#include "profile.hpp"
extern struct GPUProfile{
public:
    Tprofile copy;
    Tprofile send;
    Tprofile recv;
    Tprofile calc;
    const PS::S32 n_profile;

    GPUProfile(): 
        copy (Tprofile("copy       ")),
        send (Tprofile("send       ")),
        recv (Tprofile("receive    ")),
        calc (Tprofile("calc_force ")),
        n_profile(4) {}

	void print(std::ostream & fout, const PS::F64 time_sys, const PS::S64 n_loop=1){
        fout<<"Time: "<<time_sys<<std::endl;
        
        for(PS::S32 i=0; i<n_profile; i++) {
            Tprofile* iptr = (Tprofile*)this+i;
            iptr->print(fout, n_loop);
        }
    }

    void dump(std::ostream & fout, const PS::S32 width=20, const PS::S64 n_loop=1) const {
        for(PS::S32 i=0; i<n_profile; i++) {
            Tprofile* iptr = (Tprofile*)this+i;
            iptr->dump(fout, width, n_loop);
        }
    }

    void dumpName(std::ostream & fout, const PS::S32 width=20) {
        for(PS::S32 i=0; i<n_profile; i++) {
            Tprofile* iptr = (Tprofile*)this+i;
            iptr->dumpName(fout, width);
        }
    }
    
    void clear(){
        for(PS::S32 i=0; i<n_profile; i++) {
            Tprofile* iptr = (Tprofile*)this+i;
            iptr->reset();
        }
    }

} gpu_profile;

extern struct GPUCounter{
public:
    NumCounter n_walk;
    NumCounter n_epi;
    NumCounter n_epj;
    NumCounter n_spj;
    NumCounter n_call;
    const PS::S32 n_counter;

    GPUCounter(): 
        n_walk (NumCounter("n_walk ")),
        n_epi  (NumCounter("n_epi  ")),
        n_epj  (NumCounter("n_epj  ")),
        n_spj  (NumCounter("n_spj  ")),
        n_call (NumCounter("n_call ")),
        n_counter(5) {}

    void dump(std::ostream & fout, const PS::S32 width=20, const PS::S64 n_loop=1) const{
        for(PS::S32 i=0; i<n_counter; i++) {
            NumCounter* iptr = (NumCounter*)this+i;
            iptr->dump(fout, width, n_loop);
        }
    }
    void dumpName(std::ostream & fout, const PS::S32 width=20) const{
        for(PS::S32 i=0; i<n_counter; i++) {
            NumCounter* iptr = (NumCounter*)this+i;
            iptr->dumpName(fout, width);
        }
    }
    
    void clear() {
        for(PS::S32 i=0; i<n_counter; i++) {
            NumCounter* iptr = (NumCounter*)this+i;
            *iptr = 0;
        }
    }

} gpu_counter;
#endif

#ifdef USE_QUAD
#define SPJSoft PS::SPJQuadrupoleInAndOut
#else
#define SPJSoft PS::SPJMonopoleInAndOut
#endif

#ifdef PARTICLE_SIMULATOR_GPU_MULIT_WALK_INDEX

PS::S32 DispatchKernelWithSPIndex(const PS::S32 tag,
                                  const PS::S32 n_walk,
                                  const EPISoft ** epi,
                                  const PS::S32 *  n_epi,
                                  const PS::S32 ** id_epj,
                                  const PS::S32 *  n_epj,
                                  const PS::S32 ** id_spj,
                                  const PS::S32 *  n_spj,
                                  const EPJSoft * epj,
                                  const PS::S32 n_epj_tot,
                                  const SPJSoft * spj,
                                  const PS::S32 n_spj_tot,
                                  const bool send_flag);

#else

PS::S32 DispatchKernelWithSP(const PS::S32 tag,
                             const PS::S32 n_walk,
                             const EPISoft ** epi,
                             const PS::S32 *  n_epi,
                             const EPJSoft ** epj,
                             const PS::S32 *  n_epj,
                             const SPJSoft ** spj,
                             const PS::S32  * n_spj);

#endif

PS::S32 RetrieveKernel(const PS::S32 tag,
                       const PS::S32 n_walk,
                       const PS::S32 * ni,
                       ForceSoft      ** force);

