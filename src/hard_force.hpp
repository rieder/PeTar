#pragma once
#include "transit.h"

#ifdef HARD_DEBUG_DEEP_CHECK
#include "AR.h"
#endif

typedef double double3[3];

inline void CalcAccPotShortWithLinearCutoff(const PS::F64vec & posi,
					    PS::F64vec & acci_pla,
					    PS::F64 & poti_tot,
					    const PS::F64vec & posj,
					    const PS::F64 massj,
                        const PS::F64 mass_bkj,
                        const PS::S32 pot_control_flag,
					    const PS::F64 eps2,
					    const PS::F64 rcut_oi_inv,
                        const PS::F64 rcut_A,
                        const PS::F64 rcut_out,
					    const PS::F64 rcut_in){
    const PS::F64vec rij = posi - posj;
    const PS::F64 r2 = rij * rij;
    const PS::F64 r2_eps = r2 + eps2;
    const PS::F64 rcut2_out = rcut_out * rcut_out;
    const PS::F64 R = 1.0/sqrt(r2_eps);
    const PS::F64 Rm = massj * R;
    const PS::F64 R2 = R * R;
    const PS::F64 Rm3 = Rm * R2;
    const PS::F64 r_eps = R * r2_eps;
    const PS::F64 k = cutoff_poly_3rd(r_eps, rcut_oi_inv, rcut_A, rcut_in);
    const PS::F64 r2_max = (r2_eps > rcut2_out) ? r2_eps : rcut2_out;
    const PS::F64 R_max = 1.0/sqrt(r2_max);
    const PS::F64 Rm_max = massj * R_max;
    const PS::F64 R2_max = R_max * R_max;
    const PS::F64 Rm3_max = Rm_max * R2_max;
#ifdef ONLY_SOFT
    PS::F64 pot_off = cutoff_pot(1.0, rcut_oi_inv, rcut_A, rcut_in)/rcut_out;
    const PS::F64 kpot  = 1.0 - cutoff_pot(r_eps, rcut_oi_inv, rcut_A, rcut_in);
    if(pot_control_flag==0) poti_tot -= r2_eps>rcut2_out? 0.0: (Rm*kpot + massj*pot_off  - Rm_max);   // single, remove cutoff, obtain total potential
    else if(pot_control_flag==1) poti_tot -= r2_eps>rcut2_out? 0.0: (mass_bkj * (R*kpot + pot_off) - Rm_max); // member mass is zero, use backup value
    else poti_tot += Rm_max; // artifical, should be exclude for orbital artifical particles, since it is inside neighbor, Rm_max cancel it o
#else
    if(pot_control_flag==0) poti_tot -= (Rm - Rm_max);   // single, remove cutoff, obtain total potential
    else if(pot_control_flag==1) poti_tot -= (mass_bkj * R - Rm_max); // member mass is zero, use backup value
    else poti_tot += Rm_max; // artifical, should be exclude for orbital artifical particles, since it is inside neighbor, Rm_max cancel it out, the contribution become zero
#endif
    acci_pla -= (Rm3*(1-k) - Rm3_max)*rij;
}

#ifdef KDKDK_4TH
inline void CalcAcorrShortWithLinearCutoff(const PS::F64vec & posi,
                                           PS::F64vec & acci,
                                           PS::F64vec & acorri,
                                           const PS::F64vec & posj,
                                           const PS::F64vec & accj,
                                           const PS::F64 massj,
                                           const PS::F64 eps2,
                                           const PS::F64 rcut_oi_inv,
                                           const PS::F64 rcut_A,
                                           const PS::F64 rcut_out,
                                           const PS::F64 rcut_in) {
    const PS::F64 rcut2_out = rcut_out * rcut_out;

    const PS::F64vec rij = posi - posj;
    const PS::F64vec aij = acci - accj;
    const PS::F64 r2 = rij * rij;
    const PS::F64 r2_eps = r2 + eps2;
    const PS::F64 rijaij = rij*aij;
    const PS::F64 R = 1.0/sqrt(r2_eps);
    const PS::F64 Rm = massj * R;
    const PS::F64 R2 = R * R;
    const PS::F64 Rm3 = Rm * R2;
    const PS::F64 r_eps = R * r2_eps;

    const PS::F64 k = 1.0 - cutoff_poly_3rd(r_eps, rcut_oi_inv, rcut_A, rcut_in);
    const PS::F64 kdot = - cutoff_poly_3rd_dot(r_eps, rijaij, rcut_oi_inv, rcut_A, rcut_in);

    const PS::F64 r2_max = (r2_eps > rcut2_out) ? r2_eps : rcut2_out;
    const PS::F64 R_max = 1.0/sqrt(r2_max);
    const PS::F64 Rm_max = massj * R_max;
    const PS::F64 R2_max = R_max * R_max;
    const PS::F64 Rm3_max = Rm_max * R2_max;

    const PS::F64 alpha = rijaij * R2;
    const PS::F64 alpha_max = rijaij * R2_max;
    const PS::F64vec acorr_k = Rm3 * (k*aij - (3.0*k*alpha - kdot) * rij);
    const PS::F64vec acorr_max = Rm3_max * (aij - 3.0*alpha_max * rij);

    acorri -= 2.0 * (acorr_k - acorr_max);
    //acci + dt_kick * dt_kick * acorri /48; 
}
#endif

inline void CalcAcc0Acc1R2Cutoff(const PS::F64vec posi,
                                 const PS::F64vec veli,
                                 PS::F64vec & acci,
                                 PS::F64vec & jrki,
                                 PS::F64 & r2,
                                 const PS::F64vec posj, 
                                 const PS::F64vec velj,
                                 const PS::F64 massj,
                                 const PS::F64 eps2,
                                 const PS::F64 rcut_out,
                                 const PS::F64 rcut_in,
                                 const PS::F64 rcut_oi_inv,
                                 const PS::F64 rcut_A){
    const PS::F64vec rij = posi - posj;
    r2 = rij*rij;
    const PS::F64 r2_eps = r2 + eps2;
    if(r2_eps <= rcut_out*rcut_out){
        const PS::F64vec vij = veli - velj;
        const PS::F64 rijvij = rij * vij;
        const PS::F64 r_eps = sqrt(r2_eps);
        const PS::F64 R = 1.0/r_eps;
        //const PS::F64 R = 1.0 / sqrt(r2_eps);
        const PS::F64 R2 = R*R;
        const PS::F64 R3 = R2*R;
        const PS::F64 A = (rijvij)*R2;
        const PS::F64 K = cutoff_poly_3rd(r_eps, rcut_oi_inv, rcut_A, rcut_in);
        const PS::F64 Kdot = cutoff_poly_3rd_dot(r_eps, rijvij, rcut_oi_inv, rcut_A, rcut_in);
        const PS::F64 MR3 = massj*R3;
        const PS::F64vec F0 = -MR3*rij*K;
        const PS::F64vec F1 = -MR3*vij*K - 3.0*A*F0 - MR3*rij*Kdot;
        acci += F0;
        jrki += F1;
#ifdef HARD_DEBUG
        assert(!std::isnan(F0[0]));
        assert(!std::isnan(F0[1]));
        assert(!std::isnan(F0[2]));
        assert(!std::isnan(F1[0]));
        assert(!std::isnan(F1[1]));
        assert(!std::isnan(F1[2]));
        //assert(F0[0]==F0[0]);
        //assert(F0[1]==F0[1]);
        //assert(F0[2]==F0[2]);
        //assert(F1[0]==F1[0]);
        //assert(F1[1]==F1[1]);
        //assert(F1[2]==F1[2]);
#endif
    }
}

